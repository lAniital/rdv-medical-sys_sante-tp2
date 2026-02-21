# services/auth_service.py - Service de gestion de l'authentification et création de comptes
import sqlite3

from data.db import Database
from services.security import hash_password, verify_password


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def login(self, username: str, password: str):
        username = (username or "").strip()
        password = (password or "").strip()

        user = self.db.fetchone(
            # Case-insensitive match (consistent with COLLATE NOCASE)
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE AND active=1",
            (username,),
        )
        if user and verify_password(password, user["password_hash"]):
            return user
        return None

    def create_patient(self, username: str, password: str, email: str) -> tuple[bool, str]:
        """
        Create a PATIENT account.
        Email is required and must be unique (unique index handles it).
        Returns (ok, message) for UI.
        """
        username = (username or "").strip()
        password = (password or "").strip()
        email = (email or "").strip()

        if len(username) < 3:
            return False, "Nom d’utilisateur trop court (min 3)."
        if len(password) < 4:
            return False, "Mot de passe trop court (min 4)."
        if not email:
            return False, "Email obligatoire."

        try:
            self.db.execute(
                """
                INSERT INTO users(username, password_hash, role, active, email)
                VALUES (?, ?, 'PATIENT', 1, ?)
                """,
                (username, hash_password(password), email),
            )
            return True, "Compte créé."
        except sqlite3.IntegrityError as e:
            msg = str(e).lower()
            if "username" in msg:
                return False, "Nom d’utilisateur déjà pris."
            if "email" in msg:
                return False, "Email déjà utilisé."
            return False, "Contrainte d’unicité violée."
        except Exception:
            return False, "Erreur lors de la création du compte."

    def create_user(
        self,
        username: str,
        password: str,
        role: str,
        email: str | None = None,
        speciality: str | None = None,
    ) -> bool:
        """
        Generic creator (MEDECIN/ADMIN).
        Email optional.
        """
        try:
            self.db.execute(
                """
                INSERT INTO users(username, password_hash, role, active, email, speciality)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (username, hash_password(password), role, email, speciality),
            )
            return True
        except Exception:
            return False
