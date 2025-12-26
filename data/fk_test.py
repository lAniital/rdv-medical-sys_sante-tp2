from data.db import Database

db = Database()

try:
    db.execute("""
        INSERT INTO rdv(patient_id, medecin_id, creneau_id, status, is_urgent, urgent_reason, created_at, reminder_sent)
        VALUES (?, ?, ?, 'PREVU', 0, NULL, '2025-01-01T10:00:00', 0)
    """, (9999, 9999, 9999))  # IDs that don't exist
except Exception as e:
    print("FK working, insert blocked:", e)

db.close()
