from datetime import datetime
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
            (medecin_id,)
        )

    def book_rdv(self, patient_id: int, creneau_id: int,
                 is_urgent: bool = False, reason: str | None = None) -> bool:
        if is_urgent and (reason is None or not reason.strip()):
            return False

        try:
            # ensure slot exists + available
            slot = self.db.fetchone(
                "SELECT id, medecin_id FROM creneaux WHERE id=? AND available=1 AND blocked=0",
                (creneau_id,)
            )
            if not slot:
                return False

            medecin_id = slot["medecin_id"]

            self.db.begin()

            # create RDV
            self.db.execute("""
                INSERT INTO rdv(patient_id, medecin_id, creneau_id, status, is_urgent, urgent_reason, created_at, reminder_sent)
                VALUES (?, ?, ?, 'PREVU', ?, ?, ?, 0)
            """, (
                patient_id,
                medecin_id,
                creneau_id,
                int(is_urgent),
                reason.strip() if reason else None,
                datetime.now().isoformat()
            ), commit=False)

            # lock slot
            self.db.execute(
                "UPDATE creneaux SET available=0 WHERE id=?",
                (creneau_id,),
                commit=False
            )

            self.db.commit()
            return True

        except Exception:
            self.db.rollback()
            return False

    def list_patient_rdvs(self, patient_id: int):
        return self.db.fetchall("""
            SELECT r.id, r.status, r.is_urgent, r.urgent_reason, r.created_at,
                   u.username AS medecin_name, c.start, c.end, r.creneau_id
            FROM rdv r
            JOIN users u ON r.medecin_id = u.id
            JOIN creneaux c ON r.creneau_id = c.id
            WHERE r.patient_id = ?
            ORDER BY c.start
        """, (patient_id,))

    def cancel_rdv(self, rdv_id: int) -> bool:
        try:
            rdv = self.db.fetchone(
                "SELECT id, status, creneau_id FROM rdv WHERE id=?",
                (rdv_id,)
            )
            if not rdv or rdv["status"] == "ANNULE":
                return False

            self.db.begin()

            # cancel rdv
            self.db.execute(
                "UPDATE rdv SET status='ANNULE' WHERE id=?",
                (rdv_id,),
                commit=False
            )

            # free slot
            self.db.execute(
                "UPDATE creneaux SET available=1 WHERE id=?",
                (rdv["creneau_id"],),
                commit=False
            )

            self.db.commit()
            return True

        except Exception:
            self.db.rollback()
            return False

    def modify_rdv(self, rdv_id: int, new_creneau_id: int,
                   is_urgent: bool | None = None, reason: str | None = None) -> bool:
        """
        Modify = switch slot for same doctor.
        Logic:
          - get old rdv + old slot
          - check new slot available and belongs to same doctor
          - free old slot
          - lock new slot
          - update rdv record (change creneau_id, optionally urgent fields)
        """
        try:
            old = self.db.fetchone("""
                SELECT r.id, r.status, r.medecin_id, r.creneau_id
                FROM rdv r
                WHERE r.id=?
            """, (rdv_id,))
            if not old or old["status"] == "ANNULE":
                return False

            new_slot = self.db.fetchone("""
                SELECT id, medecin_id
                FROM creneaux
                WHERE id=? AND available=1 AND blocked=0
            """, (new_creneau_id,))
            if not new_slot:
                return False

            # must be same doctor
            if new_slot["medecin_id"] != old["medecin_id"]:
                return False

            # urgent update rules
            if is_urgent is True and (reason is None or not reason.strip()):
                return False

            self.db.begin()

            # free old slot
            self.db.execute(
                "UPDATE creneaux SET available=1 WHERE id=?",
                (old["creneau_id"],),
                commit=False
            )

            # lock new slot
            self.db.execute(
                "UPDATE creneaux SET available=0 WHERE id=?",
                (new_creneau_id,),
                commit=False
            )

            # update rdv
            if is_urgent is None:
                self.db.execute(
                    "UPDATE rdv SET creneau_id=? WHERE id=?",
                    (new_creneau_id, rdv_id),
                    commit=False
                )
            else:
                self.db.execute("""
                    UPDATE rdv
                    SET creneau_id=?,
                        is_urgent=?,
                        urgent_reason=?
                    WHERE id=?
                """, (
                    new_creneau_id,
                    int(is_urgent),
                    reason.strip() if (is_urgent and reason) else None,
                    rdv_id
                ), commit=False)

            self.db.commit()
            return True

        except Exception:
            self.db.rollback()
            return False
