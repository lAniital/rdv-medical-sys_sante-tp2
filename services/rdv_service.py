# services/rdv_service.py - Service de gestion des rendez-vous, créneaux, et agenda
from datetime import datetime, date as Date, time as Time, timedelta
from data.db import Database


class RDVService:
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

    def list_available_slots_by_date(self, medecin_id: int, day: Date | str):
        if isinstance(day, str):
            day = datetime.fromisoformat(day.strip()).date()

        day_start_dt = datetime(day.year, day.month, day.day, 0, 0, 0)
        day_end_dt = day_start_dt + timedelta(days=1)

        now_iso = datetime.now().isoformat()
        day_start_iso = day_start_dt.isoformat()
        day_end_iso = day_end_dt.isoformat()

        # if day is today -> block past hours; if future -> no need for now filter
        if day == datetime.now().date():
            min_start = now_iso
        else:
            min_start = day_start_iso

        return self.db.fetchall(
            """
            SELECT id, start, end
            FROM creneaux
            WHERE medecin_id=?
            AND available=1 AND blocked=0
            AND start >= ?
            AND start < ?
            ORDER BY start
            """,
            (medecin_id, min_start, day_end_iso),
        )

    def get_slot_by_start(self, medecin_id: int, start_iso: str):
        return self.db.fetchone(
            """
            SELECT id, start, end
            FROM creneaux
            WHERE medecin_id=?
              AND available=1 AND blocked=0
              AND start=?
            LIMIT 1
            """,
            (medecin_id, start_iso),
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

    def list_slots_for_day(self, medecin_id: int, day_iso: str):
        day = datetime.fromisoformat(day_iso.strip()).date()
        day_start = datetime(day.year, day.month, day.day, 0, 0, 0).isoformat()
        day_end = (datetime(day.year, day.month, day.day, 0, 0, 0) + timedelta(days=1)).isoformat()

        return self.db.fetchall(
            """
            SELECT id, start, end, available, blocked
            FROM creneaux
            WHERE medecin_id = ?
              AND start >= ?
              AND start < ?
            ORDER BY start
            """,
            (medecin_id, day_start, day_end),
        )

    def create_day_slots(
        self,
        medecin_id: int,
        date: str | datetime | Date,
        start: str = "08:30",
        end: str = "12:00",
        step: int = 30,
    ) -> int:
        day = self._parse_date_only(date)

        if day < datetime.now().date():
            return 0

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

    def create_day_slots_iso(
        self,
        medecin_id: int,
        day_iso: str,
        start_hhmm: str = "08:30",
        end_hhmm: str = "12:00",
        step_min: int = 30,
    ) -> int:
        return self.create_day_slots(
            medecin_id=medecin_id,
            date=day_iso,
            start=start_hhmm,
            end=end_hhmm,
            step=step_min,
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
            slot = self.db.fetchone(
                "SELECT id, medecin_id FROM creneaux WHERE id=?", (creneau_id,)
            )
            if not slot:
                return False

            medecin_id = slot["medecin_id"]

            self.db.begin()

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

    def list_patient_rdvs_upcoming(self, patient_id: int):
        now_iso = datetime.now().isoformat()
        return self.db.fetchall(
            """
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason, r.created_at,
                u.username AS medecin_name,
                c.start, c.end,
                r.creneau_id,
                u.id AS medecin_id
            FROM rdv r
            JOIN users u ON r.medecin_id = u.id
            JOIN creneaux c ON r.creneau_id = c.id
            WHERE r.patient_id = ?
            AND r.status = 'PREVU'
            AND c.start >= ?
            ORDER BY c.start ASC
            """,
            (patient_id, now_iso),
        )


    def list_patient_rdvs_canceled(self, patient_id: int):
        return self.db.fetchall(
            """
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason, r.created_at,
                u.username AS medecin_name,
                c.start, c.end,
                r.creneau_id,
                u.id AS medecin_id
            FROM rdv r
            JOIN users u ON r.medecin_id = u.id
            JOIN creneaux c ON r.creneau_id = c.id
            WHERE r.patient_id = ?
            AND r.status = 'ANNULE'
            ORDER BY c.start DESC
            """,
            (patient_id,),
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
                "UPDATE rdv SET status='ANNULE' WHERE id=?",
                (rdv_id,),
                commit=False,
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

            self.db.execute(
                "UPDATE creneaux SET available=1 WHERE id=?",
                (old["creneau_id"],),
                commit=False,
            )

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

    def get_next_rdv_within(self, patient_id: int, hours: int = 48):
        now = datetime.now()
        limit = now + timedelta(hours=hours)

        return self.db.fetchone(
            """
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason, r.reminder_sent,
                   u.username AS medecin_name,
                   c.start, c.end
            FROM rdv r
            JOIN users u ON r.medecin_id = u.id
            JOIN creneaux c ON r.creneau_id = c.id
            WHERE r.patient_id = ?
              AND r.status = 'PREVU'
              AND c.start >= ?
              AND c.start <= ?
              AND r.reminder_sent = 0
            ORDER BY c.start
            LIMIT 1
            """,
            (patient_id, now.isoformat(), limit.isoformat()),
        )

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
        
    def get_popup_reminder_for_patient(self, patient_id: int, hours: int = 48):
        if hours <= 0:
            return None

        now = datetime.now()
        limit = now + timedelta(hours=hours)

        return self.db.fetchone(
            """
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason,
                u.username AS medecin_name,
                c.start, c.end
            FROM rdv r
            JOIN users u ON r.medecin_id = u.id
            JOIN creneaux c ON r.creneau_id = c.id
            WHERE r.patient_id = ?
            AND r.status = 'PREVU'
            AND c.start >= ?
            AND c.start <= ?
            ORDER BY c.start
            LIMIT 1
            """,
            (patient_id, now.isoformat(), limit.isoformat()),
        )    

    def mark_reminder_sent(self, rdv_id: int) -> bool:
        try:
            self.db.execute("UPDATE rdv SET reminder_sent = 1 WHERE id=?", (rdv_id,))
            return True
        except Exception:
            return False

    def list_medecin_creneaux_upcoming(self, medecin_id: int):
        now_iso = datetime.now().isoformat()

        return self.db.fetchall(
            """
            SELECT
                c.id,
                c.start,
                c.end,
                c.available,
                c.blocked,
                CASE WHEN r.id IS NULL THEN 0 ELSE 1 END AS booked,
                r.id AS rdv_id,
                r.patient_id,
                u.username AS patient_username
            FROM creneaux c
            LEFT JOIN rdv r
                ON r.creneau_id = c.id
               AND r.status = 'PREVU'
            LEFT JOIN users u
                ON u.id = r.patient_id
            WHERE c.medecin_id = ?
              AND c.start >= ?
            ORDER BY c.start ASC
            """,
            (medecin_id, now_iso),
        )

    def delete_creneau_if_free(self, medecin_id: int, creneau_id: int) -> bool:
        slot = self.db.fetchone(
            "SELECT start FROM creneaux WHERE id=? AND medecin_id=?",
            (creneau_id, medecin_id),
        )
        if not slot:
            return False
        if datetime.fromisoformat(slot["start"]) <= datetime.now():
            return False

        booked = self.db.fetchone(
            "SELECT 1 FROM rdv WHERE creneau_id=? AND status='PREVU' LIMIT 1",
            (creneau_id,),
        )
        if booked:
            return False

        cur = self.db.execute(
            "DELETE FROM creneaux WHERE id=? AND medecin_id=?",
            (creneau_id, medecin_id),
        )
        return cur.rowcount > 0

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
            year=day.year,
            month=day.month,
            day=day.day,
            hour=t.hour,
            minute=t.minute,
        )
