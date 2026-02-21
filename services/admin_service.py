# services/admin_service.py - Service de gestion des médecins (admin)
import sqlite3
from data.db import Database
from services.security import hash_password
from datetime import datetime


class AdminService:
    def __init__(self, db: Database):
        self.db = db

    def list_doctors(self, include_inactive: bool = True):
        if include_inactive:
            return self.db.fetchall(
                """
                SELECT id, username, email, speciality, active
                FROM users
                WHERE role='MEDECIN'
                ORDER BY active DESC, username
                """
            )
        return self.db.fetchall(
            """
            SELECT id, username, email, speciality, active
            FROM users
            WHERE role='MEDECIN' AND active=1
            ORDER BY username
            """
        )

    def create_doctor(self, username: str, password: str, email: str, speciality: str) -> tuple[bool, str]:
        username = (username or "").strip()
        password = (password or "").strip()
        email = (email or "").strip()
        speciality = (speciality or "").strip()

        if len(username) < 3:
            return False, "Nom d’utilisateur trop court (min 3)."
        if len(password) < 4:
            return False, "Mot de passe trop court (min 4)."
        if not email:
            return False, "Email obligatoire."
        if not speciality:
            return False, "Spécialité obligatoire."

        try:
            self.db.execute(
                """
                INSERT INTO users(username, password_hash, role, active, email, speciality)
                VALUES (?, ?, 'MEDECIN', 1, ?, ?)
                """,
                (username, hash_password(password), email, speciality),
            )
            return True, "Médecin ajouté."
        except sqlite3.IntegrityError as e:
            msg = str(e).lower()
            if "username" in msg:
                return False, "Nom d’utilisateur déjà pris."
            if "email" in msg:
                return False, "Email déjà utilisé."
            return False, "Contrainte d’unicité violée."
        except Exception:
            return False, "Erreur lors de la création du médecin."

    def list_specialities(self):
        rows = self.db.fetchall(
            """
            SELECT DISTINCT speciality
            FROM users
            WHERE role='MEDECIN'
            AND speciality IS NOT NULL
            AND TRIM(speciality) != ''
            ORDER BY speciality
            """
        )
        return [r["speciality"] for r in rows]
        
    def deactivate_doctor(self, doctor_id: int) -> bool:
        try:
            self.db.execute("UPDATE users SET active=0 WHERE id=? AND role='MEDECIN'", (doctor_id,))
            return True
        except Exception:
            return False

    def reactivate_doctor(self, doctor_id: int) -> bool:
        try:
            self.db.execute("UPDATE users SET active=1 WHERE id=? AND role='MEDECIN'", (doctor_id,))
            return True
        except Exception:
            return False
    
    def doctor_has_future_rdvs(self, doctor_id: int) -> bool:
        row = self.db.fetchone(
            """
            SELECT 1
            FROM rdv r
            JOIN creneaux c ON c.id = r.creneau_id
            WHERE r.medecin_id = ?
              AND r.status = 'PREVU'
              AND c.start > ?
            LIMIT 1
            """,
            (doctor_id, datetime.now().isoformat()),
        )
        return row is not None

    def delete_doctor_hard(self, doctor_id: int) -> tuple[bool, str]:
        """
        Hard delete ONLY if doctor has no RDV history.
        Otherwise, you should deactivate instead.
        """
        row = self.db.fetchone(
            "SELECT 1 FROM rdv WHERE medecin_id = ? LIMIT 1",
            (doctor_id,),
        )
        if row:
            return False, "Impossible de supprimer: ce médecin a un historique de RDV. Utilisez Désactiver."

        try:
            self.db.execute("DELETE FROM users WHERE id=? AND role='MEDECIN'", (doctor_id,))
            return True, "Médecin supprimé."
        except Exception:
            return False, "Erreur lors de la suppression."    