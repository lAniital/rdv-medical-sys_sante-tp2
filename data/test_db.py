from data.db import Database

def main():
    db = Database()

    print("=== USERS ===")
    users = db.fetchall("SELECT id, username, role, active, password_hash FROM users")
    for u in users:
        print(dict(u))

    print("\n=== CRENEAUX ===")
    slots = db.fetchall("SELECT * FROM creneaux")
    for s in slots:
        print(dict(s))

    db.close()

if __name__ == "__main__":
    main()
