from data.db import Database
from data.setup_db import main as setup_main
from services.auth_service import AuthService
from services.rdv_service import RDVService


def main():
    # fresh DB data (your setup_db only seeds if missing; that's fine)
    setup_main()

    db = Database()
    auth = AuthService(db)
    rdv = RDVService(db)

    print("\n--- AUTH TEST (patient1 / 1234) ---")
    user = auth.login("patient1", "1234")
    print("Login OK?" , bool(user))
    if not user:
        db.close()
        return

    patient_id = user["id"]

    print("\n--- LIST DOCTORS ---")
    docs = rdv.list_medecins()
    for d in docs:
        print(dict(d))

    medecin_id = docs[0]["id"]

    print("\n--- LIST AVAILABLE SLOTS ---")
    slots = rdv.list_available_creneaux(medecin_id)
    for s in slots:
        print(dict(s))
    if not slots:
        print("No available slots to book.")
        db.close()
        return

    slot_id = slots[0]["id"]

    print("\n--- BOOK URGENT RDV ---")
    ok = rdv.book_rdv(patient_id, slot_id, is_urgent=True, reason="Fever")
    print("Booked?", ok)

    print("\n--- PATIENT RDVS AFTER BOOK ---")
    rdvs = rdv.list_patient_rdvs(patient_id)
    for r in rdvs:
        print(dict(r))

    print("\n--- CANCEL FIRST RDV ---")
    if rdvs:
        ok = rdv.cancel_rdv(rdvs[0]["id"])
        print("Canceled?", ok)

    print("\n--- PATIENT RDVS AFTER CANCEL ---")
    rdvs2 = rdv.list_patient_rdvs(patient_id)
    for r in rdvs2:
        print(dict(r))

    db.close()


if __name__ == "__main__":
    main()
