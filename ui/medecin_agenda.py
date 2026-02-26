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

        self._free_items = []
        self._booked_items = []

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

        self.nb = ttk.Notebook(body)
        self.nb.pack(fill="both", expand=True)

        self.tab_free = tk.Frame(self.nb, bg=DARK_BG)
        self.tab_booked = tk.Frame(self.nb, bg=DARK_BG)

        self.nb.add(self.tab_free, text="Libres")
        self.nb.add(self.tab_booked, text="Réservés")

        free_frame = tk.Frame(self.tab_free, bg=DARK_BG)
        free_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.list_free = tk.Listbox(free_frame, height=18)
        self.list_free.pack(side="left", fill="both", expand=True)

        sb1 = tk.Scrollbar(free_frame, orient="vertical", command=self.list_free.yview)
        sb1.pack(side="right", fill="y")
        self.list_free.config(yscrollcommand=sb1.set)

        booked_frame = tk.Frame(self.tab_booked, bg=DARK_BG)
        booked_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.list_booked = tk.Listbox(booked_frame, height=18)
        self.list_booked.pack(side="left", fill="both", expand=True)

        sb2 = tk.Scrollbar(booked_frame, orient="vertical", command=self.list_booked.yview)
        sb2.pack(side="right", fill="y")
        self.list_booked.config(yscrollcommand=sb2.set)

        btns = tk.Frame(body, bg=DARK_BG)
        btns.pack(fill="x", pady=(12, 0))

        tk.Button(
            btns,
            text="Rafraîchir",
            bg=BTN_BG,
            fg=BTN_FG,
            height=2,
            command=self.refresh,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_delete = tk.Button(
            btns,
            text="Supprimer le créneau (libre)",
            bg=BTN_BG,
            fg=BTN_FG,
            height=2,
            command=self.delete_selected_free,
        )
        self.btn_delete.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            btns,
            text="Retour",
            bg=BTN_BG,
            fg=BTN_FG,
            height=2,
            command=self.back,
        ).pack(side="left", fill="x", expand=True)

        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, _evt=None):
        tab_text = self.nb.tab(self.nb.select(), "text")
        self.btn_delete.config(state="normal" if tab_text == "Libres" else "disabled")

    def _row_value(self, row, key, default=None):
        """Safe access for sqlite3.Row (no .get())."""
        try:
            return row[key]
        except Exception:
            return default

    def _parse_dt(self, value: str) -> datetime:
        if value is None:
            raise ValueError("Datetime value is None")
        s = str(value).strip()
        try:
            return datetime.fromisoformat(s)
        except Exception:
            if "." in s:
                s = s.split(".", 1)[0]
                return datetime.fromisoformat(s)
            raise

    def refresh(self):
        self.list_free.delete(0, tk.END)
        self.list_booked.delete(0, tk.END)
        self._free_items = []
        self._booked_items = []

        try:
            rows = list(self.service.list_medecin_creneaux_upcoming(self.user["id"]))
        except Exception as e:
            self.summary_label.config(text="Erreur lors du chargement des créneaux.")
            messagebox.showerror("Erreur", f"Impossible de charger les créneaux.\n\n{e}")
            return

        if not rows:
            self.summary_label.config(text="Aucun créneau à venir.")
            self.list_free.insert(tk.END, "Aucun créneau libre.")
            self.list_booked.insert(tk.END, "Aucun créneau réservé.")
            self._on_tab_changed()
            return

        try:
            for row in rows:
                start_dt = self._parse_dt(self._row_value(row, "start"))
                end_dt = self._parse_dt(self._row_value(row, "end"))
                date_txt = start_dt.strftime("%d/%m/%Y")
                time_txt = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"

                booked = self._row_value(row, "booked", 0)

                if booked:
                    v = self._row_value(row, "is_urgent", 0)

                    # robust conversion to bool
                    if v is None:
                        is_urgent = False
                    elif isinstance(v, bool):
                        is_urgent = v
                    elif isinstance(v, (int, float)):
                        is_urgent = int(v) == 1
                    else:
                        s = str(v).strip().lower()
                        is_urgent = s in ("1", "true", "yes", "y", "urgent")

                    urgent_txt = ""
                    if is_urgent:
                        reason = (self._row_value(row, "urgent_reason", "") or "").strip()
                        urgent_txt = " | URGENT" + (f" ({reason})" if reason else "")

                    patient = self._row_value(row, "patient_username", "")
                    extra = f" | patient: {patient}{urgent_txt}"
                    line = f"{date_txt} {time_txt}{extra}"

                    self._booked_items.append(row)
                    self.list_booked.insert(tk.END, line)
                else:
                    line = f"{date_txt} {time_txt}"
                    self._free_items.append(row)
                    self.list_free.insert(tk.END, line)

        except Exception as e:
            self.summary_label.config(text="Erreur pendant l'affichage des créneaux.")
            messagebox.showerror(
                "Erreur",
                "Une erreur est survenue pendant l'affichage.\n"
                "Regarde aussi le terminal pour les détails.\n\n"
                f"{e}",
            )
            self.list_free.insert(tk.END, "Erreur d'affichage (voir message).")
            self.list_booked.insert(tk.END, "Erreur d'affichage (voir message).")
            self._on_tab_changed()
            return

        if not self._free_items:
            self.list_free.insert(tk.END, "Aucun créneau libre.")
        if not self._booked_items:
            self.list_booked.insert(tk.END, "Aucun créneau réservé.")

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
        start_dt = self._parse_dt(self._row_value(row, "start"))

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