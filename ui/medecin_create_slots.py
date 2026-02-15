import tkinter as tk
from tkinter import messagebox

from ui.theme import apply_dark, make_btn, make_label, make_entry, FONT_TITLE

class MedecinCreateSlots:
    def __init__(self, user, service, parent=None):
        self.user = user
        self.service = service

        self.win = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.win.title("Créer des créneaux")
        self.win.geometry("520x320")
        self.win.resizable(False, False)
        apply_dark(self.win)

        frame = tk.Frame(self.win, bg="#1f1f1f")
        frame.pack(expand=True, fill="both", padx=20, pady=15)

        make_label(frame, "Créer des créneaux (journée)", font=FONT_TITLE).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        make_label(frame, "Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=6)
        self.day = make_entry(frame)
        self.day.grid(row=1, column=1, sticky="ew", pady=6)

        make_label(frame, "Début (HH:MM):").grid(row=2, column=0, sticky="w", pady=6)
        self.start = make_entry(frame)
        self.start.insert(0, "08:30")
        self.start.grid(row=2, column=1, sticky="ew", pady=6)

        make_label(frame, "Fin (HH:MM):").grid(row=3, column=0, sticky="w", pady=6)
        self.end = make_entry(frame)
        self.end.insert(0, "12:00")
        self.end.grid(row=3, column=1, sticky="ew", pady=6)

        make_label(frame, "Durée (min):").grid(row=4, column=0, sticky="w", pady=6)
        self.step = make_entry(frame)
        self.step.insert(0, "30")
        self.step.grid(row=4, column=1, sticky="ew", pady=6)

        frame.grid_columnconfigure(1, weight=1)

        make_btn(frame, "Créer", self.create, width=26).grid(row=5, column=0, columnspan=2, pady=(14, 6), sticky="ew")
        make_btn(frame, "Retour", self.win.destroy, width=26).grid(row=6, column=0, columnspan=2, pady=(6, 0), sticky="ew")

    def create(self):
        day = self.day.get().strip()
        start = self.start.get().strip()
        end = self.end.get().strip()
        step = self.step.get().strip()

        try:
            step_int = int(step)
        except Exception:
            messagebox.showerror("Erreur", "Durée invalide.")
            return

        created = self.service.create_day_slots(self.user["id"], day, start, end, step_int)
        messagebox.showinfo("Info", f"Créneaux créés: {created}")
