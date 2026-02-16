from data.db import Database, init_db
from services.security import hash_password

def main():
    db = Database()
    init_db(db)

    new_password = "admin"
    db.execute(
        """
        INSERT INTO users(username, password_hash, role, active, email, speciality)
        VALUES ('admin', ?, 'ADMIN', 1, NULL, NULL)
        ON CONFLICT(username) DO UPDATE SET
            password_hash=excluded.password_hash,
            role='ADMIN',
            active=1
        """,
        (hash_password(new_password),),
    )

    db.close()
    print("Admin reset OK. username=admin password=admin")

if __name__ == "__main__":
    main()