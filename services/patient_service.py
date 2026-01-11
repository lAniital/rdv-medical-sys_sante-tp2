import tkinter as tk
from tkinter import messagebox

from data.db import Database
from services.rdv_service import RDVService
from datetime import datetime, date as Date, time as Time, timedelta


class PatientService:
    def __init__(self, db: Database):
        self.db = db

    def list_medecins(self):
        return self.db.fetchall(
            "SELECT id, username, speciality, email FROM users WHERE role='MEDECIN' AND active=1"
        )

    def list_available_creneaux(self, medecin_id: int):
        return self.db.fetchall(
            "SELECT id, start, end FROM creneaux WHERE medecin_id=? AND available=1 AND blocked=0 ORDER BY start",
            (medecin_id,),
        )

    def book_rdv(
        self,
        patient_id: int,
        creneau_id: int,
        is_urgent: bool = False,
        reason: str | None = None,
    ) -> bool:
        if is_urgent and (reason is None or not reason.strip()):
            return False

        try:
            # Check slot exists (read only)
            slot = self.db.fetchone(
                "SELECT id, medecin_id FROM creneaux WHERE id=?", (creneau_id,)
            )
            if not slot:
                return False

            medecin_id = slot["medecin_id"]

            self.db.begin()

            # 1) Lock slot first (atomic)
            cur = self.db.execute(
                """
                UPDATE creneaux
                SET available=0
                WHERE id=? AND available=1 AND blocked=0
            """,
                (creneau_id,),
                commit=False,
            )

            if cur.rowcount != 1:
                self.db.rollback()
                return False

            # 2) Insert RDV only after the lock succeeded
            self.db.execute(
                """
                INSERT INTO rdv(patient_id, medecin_id, creneau_id, status, is_urgent, urgent_reason, created_at, reminder_sent)
                VALUES (?, ?, ?, 'PREVU', ?, ?, ?, 0)
            """,
                (
                    patient_id,
                    medecin_id,
                    creneau_id,
                    int(is_urgent),
                    reason.strip() if reason else None,
                    datetime.now().isoformat(),
                ),
                commit=False,
            )

            self.db.commit()
            return True

        except Exception:
            self.db.rollback()
            return False

    def list_patient_rdvs(self, patient_id: int, include_canceled: bool = True):
        where = "WHERE r.patient_id = ?"
        params = [patient_id]

        if not include_canceled:
            where += " AND r.status != 'ANNULE'"

        return self.db.fetchall(
            f"""
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason, r.created_at,
                   u.username AS medecin_name,
                   c.start, c.end,
                   r.creneau_id,
                   u.id AS medecin_id
            FROM rdv r
            JOIN users u ON r.medecin_id = u.id
            JOIN creneaux c ON r.creneau_id = c.id
            {where}
            ORDER BY c.start
        """,
            tuple(params),
        )

    def list_doctor_agenda(self, medecin_id: int, include_canceled: bool = False):
        where = "WHERE r.medecin_id = ?"
        params = [medecin_id]

        if not include_canceled:
            where += " AND r.status != 'ANNULE'"

        return self.db.fetchall(
            f"""
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason, r.created_at,
                   p.username AS patient_name,
                   c.start, c.end,
                   r.creneau_id,
                   p.id AS patient_id
            FROM rdv r
            JOIN users p ON r.patient_id = p.id
            JOIN creneaux c ON r.creneau_id = c.id
            {where}
            ORDER BY c.start
        """,
            tuple(params),
        )

    def cancel_rdv(self, rdv_id: int) -> bool:
        try:
            rdv = self.db.fetchone(
                "SELECT id, status, creneau_id FROM rdv WHERE id=?", (rdv_id,)
            )
            if not rdv or rdv["status"] == "ANNULE":
                return False

            self.db.begin()

            self.db.execute(
                "UPDATE rdv SET status='ANNULE' WHERE id=?", (rdv_id,), commit=False
            )

            self.db.execute(
                "UPDATE creneaux SET available=1 WHERE id=?",
                (rdv["creneau_id"],),
                commit=False,
            )

            self.db.commit()
            return True

        except Exception:
            self.db.rollback()
            return False

    def modify_rdv(self, rdv_id: int, new_creneau_id: int) -> bool:
        try:
            old = self.db.fetchone(
                """
                SELECT r.id, r.status, r.medecin_id, r.creneau_id
                FROM rdv r
                WHERE r.id=?
            """,
                (rdv_id,),
            )
            if not old or old["status"] == "ANNULE":
                return False

            # Validate new slot belongs to same doctor (read only)
            new_slot = self.db.fetchone(
                """
                SELECT id, medecin_id
                FROM creneaux
                WHERE id=?
            """,
                (new_creneau_id,),
            )
            if not new_slot:
                return False
            if new_slot["medecin_id"] != old["medecin_id"]:
                return False

            self.db.begin()

            # 1) Lock new slot first (atomic)
            cur = self.db.execute(
                """
                UPDATE creneaux
                SET available=0
                WHERE id=? AND available=1 AND blocked=0
            """,
                (new_creneau_id,),
                commit=False,
            )

            if cur.rowcount != 1:
                self.db.rollback()
                return False

            # 2) Free old slot only after new one is locked
            self.db.execute(
                "UPDATE creneaux SET available=1 WHERE id=?",
                (old["creneau_id"],),
                commit=False,
            )

            # 3) Update RDV after both slot updates
            self.db.execute(
                "UPDATE rdv SET creneau_id=? WHERE id=?",
                (new_creneau_id, rdv_id),
                commit=False,
            )

            self.db.commit()
            return True

        except Exception:
            self.db.rollback()
            return False

    def create_day_slots(
        self,
        medecin_id: int,
        date: str | datetime | Date,
        start: str = "08:30",
        end: str = "12:00",
        step: int = 30,
    ) -> int:
        day = self._parse_date_only(date)
        start_dt = self._combine_date_time(day, self._parse_hhmm(start))
        end_dt = self._combine_date_time(day, self._parse_hhmm(end))

        if step <= 0 or end_dt <= start_dt:
            return 0

        created = 0
        cursor_dt = start_dt

        try:
            self.db.begin()

            while cursor_dt + timedelta(minutes=step) <= end_dt:
                s = cursor_dt
                e = cursor_dt + timedelta(minutes=step)

                # FIX: do NOT pass commit=False (db.fetchone doesn't have that parameter)
                exists = self.db.fetchone(
                    """
                    SELECT id FROM creneaux
                    WHERE medecin_id=? AND start=? AND end=?
                """,
                    (medecin_id, s.isoformat(), e.isoformat()),
                )

                if not exists:
                    self.db.execute(
                        """
                        INSERT INTO creneaux(medecin_id, start, end, available, blocked)
                        VALUES (?, ?, ?, 1, 0)
                    """,
                        (medecin_id, s.isoformat(), e.isoformat()),
                        commit=False,
                    )
                    created += 1

                cursor_dt = e

            self.db.commit()
            return created

        except Exception:
            self.db.rollback()
            return 0

    # --- replace get_reminder_for_patient with this ---
    def get_reminder_for_patient(self, patient_id: int, hours: int = 48):
        if hours <= 0:
            return None

        now = datetime.now()
        limit = now + timedelta(hours=hours)

        return self.db.fetchone(
            """
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason, r.reminder_sent,
                   u.username AS medecin_name,
                   c.start, c.end,
                   r.creneau_id
            FROM rdv r
            JOIN users u ON r.medecin_id = u.id
            JOIN creneaux c ON r.creneau_id = c.id
            WHERE r.patient_id = ?
              AND r.status = 'PREVU'
              AND r.reminder_sent = 0
              AND c.start >= ?
              AND c.start <= ?
            ORDER BY c.start
            LIMIT 1
        """,
            (patient_id, now.isoformat(), limit.isoformat()),
        )

    def mark_reminder_sent(self, rdv_id: int) -> None:
        self.db.execute("UPDATE rdv SET reminder_sent=1 WHERE id=?", (rdv_id,))

    # Helpers
    def _parse_hhmm(self, hhmm: str) -> Time:
        hhmm = (hhmm or "").strip()
        parts = hhmm.split(":")
        if len(parts) != 2:
            raise ValueError("Time must be HH:MM")
        return Time(hour=int(parts[0]), minute=int(parts[1]))

    def _parse_date_only(self, d: str | datetime | Date) -> Date:
        if isinstance(d, Date) and not isinstance(d, datetime):
            return d
        if isinstance(d, datetime):
            return d.date()
        return datetime.fromisoformat(d.strip()).date()

    def _combine_date_time(self, day: Date, t: Time) -> datetime:
        return datetime(
            year=day.year, month=day.month, day=day.day, hour=t.hour, minute=t.minute
        )
