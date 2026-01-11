# services/auth_service.py
from data.db import Database
from services.security import hash_password, verify_password


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def login(self, username: str, password: str):
        username = (username or "").strip()
        password = (password or "").strip()

        user = self.db.fetchone(
            "SELECT * FROM users WHERE username=? AND active=1",
            (username,),
        )
        if user and verify_password(password, user["password_hash"]):
            return user
        return None

    def create_patient(self, username: str, password: str) -> bool:
        username = (username or "").strip()
        password = (password or "").strip()

        if len(username) < 3 or len(password) < 4:
            return False

        try:
            self.db.execute(
                """
                INSERT INTO users(username, password_hash, role, active)
                VALUES (?, ?, 'PATIENT', 1)
            """,
                (username, hash_password(password)),
            )
            return True
        except Exception:
            return False

    # Optional: keep your generic method if other roles still need it
    def create_user(
        self,
        username: str,
        password: str,
        role: str,
        email: str | None = None,
        speciality: str | None = None,
    ) -> bool:
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
