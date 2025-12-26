from data.db import Database
from services.security import verify_password, hash_password


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def login(self, username: str, password: str):
        user = self.db.fetchone(
            "SELECT * FROM users WHERE username=? AND active=1",
            (username,)
        )
        if user and verify_password(password, user["password_hash"]):
            return user
        return None

    def create_user(self, username: str, password: str, role: str,
                    email: str | None = None, speciality: str | None = None) -> bool:
        try:
            self.db.execute("""
                INSERT INTO users(username, password_hash, role, active, email, speciality)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (username, hash_password(password), role, email, speciality))
            return True
        except Exception:
            return False
