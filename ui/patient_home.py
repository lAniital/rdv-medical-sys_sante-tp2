# ui/patient_home.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

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
        apply_theme(self.win)  # IMPORTANT: same theme as login

        self.win.title("Espace Patient")
        self.win.geometry("600x400")
        self.win.protocol("WM_DELETE_WINDOW", self.logout)  # treat X as logout

        #  Reminder card (hidden by default)
        self.reminder_frame = tk.Frame(self.win, bg="#2b2b2b", bd=1, relief="solid")
        self.reminder_frame.pack(fill="x", padx=16, pady=(12, 6))

        self.reminder_label = tk.Label(self.reminder_frame, text="", bg="#2b2b2b", fg="white")
        self.reminder_label.pack(side="left", padx=10, pady=10)

        self.reminder_btn = tk.Button(self.reminder_frame, text="OK", command=self.dismiss_reminder)
        self.reminder_btn.pack(side="right", padx=10, pady=10)

        self.reminder_frame.pack_forget()  # hidden by default
        self._current_reminder_id = None

        # Layout
        title = tk.Label(self.win, text=f"Bienvenue {user['username']}", font=("Segoe UI", 18, "bold"))
        title.pack(pady=25)

        btn1 = tk.Button(self.win, text="Prendre un rendez-vous", width=30, height=2, command=self.open_booking)
        btn1.pack(pady=10)

        btn2 = tk.Button(self.win, text="Gérer mes rendez-vous", width=30, height=2, command=self.open_manage)
        btn2.pack(pady=10)

        btn3 = tk.Button(self.win, text="Se déconnecter", width=30, height=2, command=self.logout)
        btn3.pack(pady=20)

        # call once on login (card UI)
        self.refresh_reminder()

        # popup once on opening (does not rely on reminder_sent)
        rem = self.service.get_popup_reminder_for_patient(self.user["id"], hours=48)
        if rem:
            start_dt = datetime.fromisoformat(rem["start"])
            urgent_txt = " (URGENT)" if int(rem["is_urgent"]) == 1 else ""
            msg = (
                f"Rappel: RDV dans 48h avec Dr {rem['medecin_name']} le "
                f"{start_dt.strftime('%d/%m/%Y %H:%M')}{urgent_txt}"
            )
            messagebox.showinfo("Rappel", msg)

    # ---------------- Reminder (card) ----------------

    def refresh_reminder(self):
        r = self.service.get_next_rdv_within(self.user["id"], hours=48)
        if not r:
            self._current_reminder_id = None
            self.reminder_frame.pack_forget()
            return

        start_dt = datetime.fromisoformat(r["start"])
        msg = f"Rappel: RDV dans 48h avec Dr {r['medecin_name']} le {start_dt.strftime('%d/%m/%Y %H:%M')}"
        if r["is_urgent"]:
            msg += " | URGENT"

        self._current_reminder_id = r["id"]
        self.reminder_label.config(text=msg)
        self.reminder_frame.pack(fill="x", padx=16, pady=(12, 6))

    def dismiss_reminder(self):
        if self._current_reminder_id:
            self.service.mark_reminder_sent(self._current_reminder_id)
        self._current_reminder_id = None
        self.reminder_frame.pack_forget()

    # ---------------- Actions ----------------

    def open_booking(self):
        PatientBookingWindow(self.user, parent=self.win)
        # refresh after booking window closes (best-effort)
        self.win.after(300, self.refresh_reminder)

    def open_manage(self):
        PatientManageWindow(self.user, parent=self.win)
        # refresh after manage window closes (best-effort)
        self.win.after(300, self.refresh_reminder)

    def logout(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()
        if self.on_logout:
            self.on_logout()