import tkinter as tk
from tkinter import messagebox

from data.db import Database
from services.rdv_service import RDVService
from ui.theme import apply_dark, make_btn, make_label, FONT_TITLE

class MedecinView:
    def __init__(self, user, on_logout=None):
        self.user = user
        self.on_logout = on_logout

        self.db = Database()
        self.service = RDVService(self.db)

        self.win = tk.Toplevel()
        self.win.title("Espace Médecin")
        self.win.geometry("520x320")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.logout)

        apply_dark(self.win)

        frame = tk.Frame(self.win, bg="#1f1f1f")
        frame.pack(expand=True, fill="both", padx=20, pady=15)

        make_label(frame, f"Espace Médecin — Dr {user['username']}", font=FONT_TITLE).pack(anchor="w", pady=(0, 12))

        make_btn(frame, "Voir mon agenda", self.open_agenda, width=30).pack(fill="x", pady=6)
        make_btn(frame, "Créer des créneaux (journée)", self.open_create_slots, width=30).pack(fill="x", pady=6)

        make_btn(frame, "Se déconnecter", self.logout, width=30).pack(fill="x", pady=(18, 0))

    def open_agenda(self):
        from ui.medecin_agenda import MedecinAgenda
        MedecinAgenda(self.user, self.win)

    def open_create_slots(self):
        from ui.medecin_create_slots import MedecinCreateSlots
        MedecinCreateSlots(self.user, self.service, parent=self.win)

    def logout(self):
        try:
            self.db.close()
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass
        if self.on_logout:
            self.on_logout()

        
        