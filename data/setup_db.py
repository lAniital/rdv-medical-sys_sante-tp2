from datetime import datetime, timedelta

from data.db import Database, init_db
from services.security import hash_password

def seed_users(db: Database) -> None:
    users = [
        ("admin", "admin", "ADMIN", None, None),
        ("dupont", "1234", "MEDECIN", "dupont@mail.com", "Généraliste"),
        ("patient1", "1234", "PATIENT", "patient1@mail.com", None),
    ]

    for username, plain_pwd, role, email, speciality in users:
        exists = db.fetchone("SELECT 1 FROM users WHERE username=?", (username,))
        if not exists:
            db.execute("""
                INSERT INTO users(username, password_hash, role, active, email, speciality)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (username, hash_password(plain_pwd), role, email, speciality))


def seed_creneaux(db: Database) -> None:
    # Find doctor id
    doc = db.fetchone("SELECT id FROM users WHERE username='dupont' AND role='MEDECIN'")
    if not doc:
        return

    medecin_id = doc["id"]

    # Insert demo slots only if none exist
    existing = db.fetchone("SELECT 1 FROM creneaux WHERE medecin_id=?", (medecin_id,))
    if existing:
        return

    now = datetime.now().replace(second=0, microsecond=0)

    slot1_start = (now + timedelta(days=1)).replace(hour=9, minute=0)
    slot1_end   = slot1_start + timedelta(minutes=30)

    slot2_start = (now + timedelta(days=2)).replace(hour=10, minute=0)
    slot2_end   = slot2_start + timedelta(minutes=30)

    db.execute("""
        INSERT INTO creneaux(medecin_id, start, end, available, blocked)
        VALUES (?, ?, ?, 1, 0)
    """, (medecin_id, slot1_start.isoformat(), slot1_end.isoformat()))

    db.execute("""
        INSERT INTO creneaux(medecin_id, start, end, available, blocked)
        VALUES (?, ?, ?, 1, 0)
    """, (medecin_id, slot2_start.isoformat(), slot2_end.isoformat()))


def main():
    db = Database()
    init_db(db)
    seed_users(db)
    seed_creneaux(db)
    db.close()
    print("DB ready: data/rdv_medical.db (hashed passwords + FK ON + unique slots)")

if __name__ == "__main__":
    main()
