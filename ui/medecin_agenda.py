# ui/medecin_agenda.py - Affiche les créneaux à venir du médecin, séparés en libres et réservés, avec possibilité de supprimer un créneau libre
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
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
    Affiche les créneaux à venir en 2 sections:
    - Libres
    - Réservés
    Permet de supprimer uniquement un créneau libre.
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

        # data
        self._free_items = []
        self._booked_items = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = tk.Frame(self.win, bg=DARK_BG)
        top.pack(fill="x", padx=16, pady=(12, 8))

        tk.Label(
            top, text="Agenda (créneaux à venir)",
            bg=DARK_BG, fg=DARK_FG, font=("Segoe UI", 16, "bold")
        ).pack(anchor="w")

        self.summary_label = tk.Label(
            top, text="",
            bg=DARK_BG, fg=DARK_FG, font=("Segoe UI", 10)
        )
        self.summary_label.pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.win, bg=DARK_BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Notebook: Libres / Réservés
        self.nb = ttk.Notebook(body)
        self.nb.pack(fill="both", expand=True)

        self.tab_free = tk.Frame(self.nb, bg=DARK_BG)
        self.tab_booked = tk.Frame(self.nb, bg=DARK_BG)

        self.nb.add(self.tab_free, text="Libres")
        self.nb.add(self.tab_booked, text="Réservés")

        # FREE list
        free_frame = tk.Frame(self.tab_free, bg=DARK_BG)
        free_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.list_free = tk.Listbox(free_frame, height=18)
        self.list_free.pack(side="left", fill="both", expand=True)

        sb1 = tk.Scrollbar(free_frame, orient="vertical", command=self.list_free.yview)
        sb1.pack(side="right", fill="y")
        self.list_free.config(yscrollcommand=sb1.set)

        # BOOKED list
        booked_frame = tk.Frame(self.tab_booked, bg=DARK_BG)
        booked_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.list_booked = tk.Listbox(booked_frame, height=18)
        self.list_booked.pack(side="left", fill="both", expand=True)

        sb2 = tk.Scrollbar(booked_frame, orient="vertical", command=self.list_booked.yview)
        sb2.pack(side="right", fill="y")
        self.list_booked.config(yscrollcommand=sb2.set)

        # Buttons bottom
        btns = tk.Frame(body, bg=DARK_BG)
        btns.pack(fill="x", pady=(12, 0))

        tk.Button(
            btns, text="Rafraîchir", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.refresh
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_delete = tk.Button(
            btns, text="Supprimer le créneau (libre)", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.delete_selected_free
        )
        self.btn_delete.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            btns, text="Retour", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.back
        ).pack(side="left", fill="x", expand=True)

        # If user switches tab, keep delete behavior consistent
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, _evt=None):
        tab_text = self.nb.tab(self.nb.select(), "text")
        # Only allow delete on "Libres" tab
        if tab_text == "Libres":
            self.btn_delete.config(state="normal")
        else:
            self.btn_delete.config(state="disabled")

    def refresh(self):
        self.list_free.delete(0, tk.END)
        self.list_booked.delete(0, tk.END)
        self._free_items = []
        self._booked_items = []

        rows = list(self.service.list_medecin_creneaux_upcoming(self.user["id"]))

        if not rows:
            self.summary_label.config(text="Aucun créneau à venir.")
            self.list_free.insert(tk.END, "Aucun créneau libre.")
            self.list_booked.insert(tk.END, "Aucun créneau réservé.")
            return

        for row in rows:
            start_dt = datetime.fromisoformat(row["start"])
            end_dt = datetime.fromisoformat(row["end"])
            date_txt = start_dt.strftime("%d/%m/%Y")
            time_txt = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"

            if row["booked"]:
                extra = f" | patient: {row['patient_username']}"
                line = f"{date_txt} {time_txt}{extra}"
                self._booked_items.append(row)
                self.list_booked.insert(tk.END, line)
            else:
                line = f"{date_txt} {time_txt}"
                self._free_items.append(row)
                self.list_free.insert(tk.END, line)

        self.summary_label.config(
            text=f"Total: {len(rows)} | Libres: {len(self._free_items)} | Réservés: {len(self._booked_items)}"
        )
        self._on_tab_changed()

    def delete_selected_free(self):
        if not self._free_items:
            messagebox.showinfo("Info", "Aucun créneau libre à supprimer.")
            return

        idxs = self.list_free.curselection()
        if not idxs:
            messagebox.showwarning("Info", "Sélectionnez un créneau libre.")
            return

        idx = int(idxs[0])
        if idx >= len(self._free_items):
            return

        row = self._free_items[idx]

        start_dt = datetime.fromisoformat(row["start"])
        if start_dt <= datetime.now():
            messagebox.showerror("Erreur", "Impossible: créneau déjà passé.")
            return

        ok = messagebox.askyesno("Confirmation", "Supprimer ce créneau libre ?")
        if not ok:
            return

        deleted = self.service.delete_creneau_if_free(self.user["id"], row["id"])
        if not deleted:
            messagebox.showerror("Erreur", "Suppression impossible (introuvable ou devenu réservé).")
            return

        messagebox.showinfo("OK", "Créneau supprimé.")
        self.refresh()

    def back(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()