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
        self.win.geometry("900x560")
        self.win.minsize(820, 520)
        self.win.resizable(True, True)
        self.win.configure(bg=DARK_BG)
        self.win.protocol("WM_DELETE_WINDOW", self.back)

        self._items = []  # rows from db

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = tk.Frame(self.win, bg=DARK_BG)
        top.pack(fill="x", padx=16, pady=(12, 8))

        tk.Label(
            top,
            text="Agenda (créneaux à venir)",
            bg=DARK_BG,
            fg=DARK_FG,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        self.summary_label = tk.Label(
            top,
            text="",
            bg=DARK_BG,
            fg=DARK_FG,
            font=("Segoe UI", 10),
        )
        self.summary_label.pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.win, bg=DARK_BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # List area with scrollbar
        list_frame = tk.Frame(body, bg=DARK_BG)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, height=18)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Buttons
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
            self.summary_label.config(text="Aucun créneau à venir.")
            self.listbox.insert(tk.END, "Aucun créneau à venir.")
            return

        free_count = sum(1 for r in self._items if not r["booked"])
        booked_count = len(self._items) - free_count
        self.summary_label.config(
            text=f"Total: {len(self._items)} | Libres: {free_count} | Réservés: {booked_count}"
        )

        for row in self._items:
            start_dt = datetime.fromisoformat(row["start"])
            end_dt = datetime.fromisoformat(row["end"])

            date_txt = start_dt.strftime("%d/%m/%Y")
            time_txt = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"

            if row["booked"]:
                status_txt = "RÉSERVÉ"
                extra = f" (patient: {row['patient_username']})"
            else:
                status_txt = "LIBRE"
                extra = ""

            # Cleaner display (no #id in UI)
            line = f"{date_txt} {time_txt} | {status_txt}{extra}"
            self.listbox.insert(tk.END, line)

    def delete_selected(self):
        if not self._items:
            return

        idxs = self.listbox.curselection()
        if not idxs:
            messagebox.showwarning("Info", "Sélectionnez un créneau.")
            return

        idx = int(idxs[0])
        if idx >= len(self._items):
            return

        row = self._items[idx]

        if row["booked"]:
            messagebox.showerror("Erreur", "Impossible: créneau déjà réservé.")
            return

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