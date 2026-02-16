import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from data.db import Database
from services.rdv_service import RDVService
from ui.theme import apply_theme

DARK_BG = "#1f1f1f"
DARK_FG = "#ffffff"
BTN_BG = "#e6e6e6"
BTN_FG = "#000000"


class MedecinAgenda:
    """
    Affiche les créneaux créés (à venir) + permet de supprimer un créneau libre.
    """
    def __init__(self, user: dict, parent: tk.Tk | tk.Toplevel):
        self.user = user
        self.parent = parent

        self.db = Database()
        self.service = RDVService(self.db)

        self.win = tk.Toplevel(parent)
        apply_theme(self.win)
        self.win.title("Mon agenda (créneaux)")
        self.win.geometry("820x520")
        self.win.configure(bg=DARK_BG)
        self.win.protocol("WM_DELETE_WINDOW", self.back)

        self._items = []  # rows from db

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = tk.Frame(self.win, bg=DARK_BG)
        top.pack(fill="x", padx=16, pady=10)

        tk.Label(
            top,
            text="Agenda (créneaux à venir)",
            bg=DARK_BG,
            fg=DARK_FG,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        body = tk.Frame(self.win, bg=DARK_BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.listbox = tk.Listbox(body, height=18, width=110)
        self.listbox.pack(fill="both", expand=True)

        btns = tk.Frame(body, bg=DARK_BG)
        btns.pack(fill="x", pady=(12, 0))

        tk.Button(
            btns, text="Rafraîchir", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.refresh
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            btns, text="Supprimer le créneau", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.delete_selected
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            btns, text="Retour", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.back
        ).pack(side="left", fill="x", expand=True)

    def refresh(self):
        self.listbox.delete(0, tk.END)
        self._items = list(self.service.list_medecin_creneaux_upcoming(self.user["id"]))

        if not self._items:
            self.listbox.insert(tk.END, "Aucun créneau à venir.")
            return

        for row in self._items:
            start_dt = datetime.fromisoformat(row["start"])
            end_dt = datetime.fromisoformat(row["end"])

            status = "LIBRE"
            extra = ""
            if row["booked"]:
                status = "RÉSERVÉ"
                extra = f" (patient: {row['patient_username']})"

            line = f"#{row['id']} | {start_dt.strftime('%Y-%m-%d %H:%M')} → {end_dt.strftime('%H:%M')} | {status}{extra}"
            self.listbox.insert(tk.END, line)

    def delete_selected(self):
        if not self._items:
            return

        idxs = self.listbox.curselection()
        if not idxs:
            messagebox.showwarning("Info", "Sélectionnez un créneau.")
            return

        idx = idxs[0]
        if idx >= len(self._items):
            return

        row = self._items[idx]

        # si réservé => interdit
        if row["booked"]:
            messagebox.showerror("Erreur", "Impossible: créneau déjà réservé.")
            return

        # si start déjà passé (sécurité)
        start_dt = datetime.fromisoformat(row["start"])
        if start_dt <= datetime.now():
            messagebox.showerror("Erreur", "Impossible: créneau déjà passé.")
            return

        ok = messagebox.askyesno("Confirmation", "Supprimer ce créneau ?")
        if not ok:
            return

        deleted = self.service.delete_creneau_if_free(self.user["id"], row["id"])
        if not deleted:
            messagebox.showerror("Erreur", "Suppression impossible (créneau réservé ou introuvable).")
            return

        messagebox.showinfo("OK", "Créneau supprimé.")
        self.refresh()

    def back(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()
