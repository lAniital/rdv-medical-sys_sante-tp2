import sqlite3
from pathlib import Path
from typing import Any, Iterable

DB_PATH = Path("data") / "rdv_medical.db"


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

    def execute(self, sql: str, params: Iterable[Any] = (), commit: bool = True):
        self.cur.execute(sql, params)
        if commit:
            self.conn.commit()
        return self.cur

    def fetchone(self, sql: str, params: Iterable[Any] = ()):
        self.cur.execute(sql, params)
        return self.cur.fetchone()

    def fetchall(self, sql: str, params: Iterable[Any] = ()):
        self.cur.execute(sql, params)
        return self.cur.fetchall()

    # Transaction helpers
    def begin(self):
        self.conn.execute("BEGIN IMMEDIATE")

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def init_db(db: Database) -> None:
    # USERS
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('PATIENT','MEDECIN','ADMIN')),
            active INTEGER NOT NULL DEFAULT 1,
            email TEXT,
            speciality TEXT
        );
        """
    )

    # Enforce unique username (case-insensitive because column uses COLLATE NOCASE)
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username
        ON users(username);
        """
    )

    # Unique email only when email is not null (allows many NULL)
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email
        ON users(email)
        WHERE email IS NOT NULL;
        """
    )

    # CRENEAUX
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS creneaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medecin_id INTEGER NOT NULL,
            start TEXT NOT NULL,
            end TEXT NOT NULL,
            available INTEGER NOT NULL DEFAULT 1,
            blocked INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (medecin_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(medecin_id, start, end)
        );
        """
    )

    # RDV
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS rdv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            medecin_id INTEGER NOT NULL,
            creneau_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'PREVU' CHECK(status IN ('PREVU','ANNULE')),
            is_urgent INTEGER NOT NULL DEFAULT 0,
            urgent_reason TEXT,
            created_at TEXT NOT NULL,
            reminder_sent INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (medecin_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (creneau_id) REFERENCES creneaux(id) ON DELETE RESTRICT
        );
        """
    )
