import sqlite3
from typing import Any, Iterable
from pathlib import Path

DB_PATH = Path("data") / "rdv_medical.db"

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)

        # IMPORTANT: enforce foreign keys in SQLite
        self.conn.execute("PRAGMA foreign_keys = ON;")

        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

    def execute(self, sql: str, param: Iterable[Any] = ()):
        self.cur.execute(sql, param)
        self.conn.commit()
        return self.cur

    def fetchone(self, sql: str, param: Iterable[Any] = ()):
        self.cur.execute(sql, param)
        return self.cur.fetchone()

    def fetchall(self, sql: str, param: Iterable[Any] = ()):
        self.cur.execute(sql, param)
        return self.cur.fetchall()

    def close(self):
        self.conn.close()


def init_db(db: Database) -> None:
    # USERS: patient/medecin/admin
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('PATIENT','MEDECIN','ADMIN')),
        active INTEGER NOT NULL DEFAULT 1,
        email TEXT,
        speciality TEXT
    );
    """)

    # CRENEAUX: availability slots
    db.execute("""
    CREATE TABLE IF NOT EXISTS creneaux (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medecin_id INTEGER NOT NULL,
        start TEXT NOT NULL, -- ISO datetime string
        end TEXT NOT NULL,   -- ISO datetime string
        available INTEGER NOT NULL DEFAULT 1,
        blocked INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (medecin_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(medecin_id, start, end)
    );
    """)

    # RDV: appointments
    db.execute("""
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
    """)
