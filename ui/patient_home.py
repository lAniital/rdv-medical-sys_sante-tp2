import tkinter as tk
from tkinter import messagebox

from ui.theme import apply_theme
from data.db import Database
from services.rdv_service import RDVService
from ui.patient_booking import PatientBookingWindow
from ui.patient_manage import PatientManageWindow



class PatientHome:
    def __init__(self, user: dict, on_logout=None):
        self.user = user
        self.on_logout = on_logout

        self.db = Database()
        self.service = RDVService(self.db)

        self.win = tk.Toplevel()
        apply_theme(self.win) # IMPORTANT: same theme as login
        
        self.win.title("Espace Patient")
        self.win.geometry("600x400")
        self.win.protocol("WM_DELETE_WINDOW", self.logout)  # treat X as logout

        # Layout
        title = tk.Label(self.win, text=f"Bienvenue {user['username']}", font=("Segoe UI", 18, "bold"))
        title.pack(pady=25)

        btn1 = tk.Button(self.win, text="Prendre un rendez-vous", width=30, height=2, command=self.open_booking)
        btn1.pack(pady=10)

        btn2 = tk.Button(self.win, text="Gérer mes rendez-vous", width=30, height=2, command=self.open_manage)
        btn2.pack(pady=10)

        btn3 = tk.Button(self.win, text="Se déconnecter", width=30, height=2, command=self.logout)
        btn3.pack(pady=20)

        # Reminder popup (next 48h)
        self.show_reminder_if_any()

    def show_reminder_if_any(self):
        rdv = self.service.get_reminder_for_patient(self.user["id"], hours=48)
        if rdv:
            messagebox.showinfo(
                "Rappel",
                f"Vous avez un rendez-vous bientôt :\n"
                f"Dr {rdv['medecin_name']}\n"
                f"{rdv['start']} → {rdv['end']}"
            )

    def open_booking(self):
        from ui.patient_booking import PatientBookingWindow
        PatientBookingWindow(self.user, parent=self.win)

    def open_manage(self):
        from ui.patient_manage import PatientManageWindow
        PatientManageWindow(self.user, parent=self.win)

    def logout(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()
        if self.on_logout:
            self.on_logout()
