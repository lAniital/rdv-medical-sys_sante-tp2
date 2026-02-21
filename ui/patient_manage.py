# ui/patient_manage.py - Gestion des RDV patient (onglets: à venir / annulés)
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


class PatientManageWindow:
    """
    Affiche les RDV du patient en 2 onglets:
    - À venir (PREVU + start >= now)
    - Annulés (ANNULE)
    Permet d'annuler uniquement un RDV à venir.
    """
    def __init__(self, user: dict, parent: tk.Tk | tk.Toplevel):
        self.user = user
        self.parent = parent

        self.db = Database()
        self.service = RDVService(self.db)

        self.win = tk.Toplevel(parent)
        apply_theme(self.win)
        self.win.title("Gérer mes rendez-vous")
        self.win.geometry("920x560")
        self.win.minsize(820, 520)
        self.win.resizable(True, True)
        self.win.configure(bg=DARK_BG)
        self.win.protocol("WM_DELETE_WINDOW", self.back)

        # data caches
        self._upcoming = []
        self._canceled = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = tk.Frame(self.win, bg=DARK_BG)
        top.pack(fill="x", padx=16, pady=(12, 8))

        tk.Label(
            top,
            text="Mes rendez-vous",
            bg=DARK_BG,
            fg=DARK_FG,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        self.summary = tk.Label(top, text="", bg=DARK_BG, fg=DARK_FG, font=("Segoe UI", 10))
        self.summary.pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.win, bg=DARK_BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.nb = ttk.Notebook(body)
        self.nb.pack(fill="both", expand=True)

        self.tab_upcoming = tk.Frame(self.nb, bg=DARK_BG)
        self.tab_canceled = tk.Frame(self.nb, bg=DARK_BG)

        self.nb.add(self.tab_upcoming, text="À venir")
        self.nb.add(self.tab_canceled, text="Annulés")

        # Upcoming list
        up_frame = tk.Frame(self.tab_upcoming, bg=DARK_BG)
        up_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.list_upcoming = tk.Listbox(up_frame, height=18)
        self.list_upcoming.pack(side="left", fill="both", expand=True)

        sb1 = tk.Scrollbar(up_frame, orient="vertical", command=self.list_upcoming.yview)
        sb1.pack(side="right", fill="y")
        self.list_upcoming.config(yscrollcommand=sb1.set)

        # Canceled list
        can_frame = tk.Frame(self.tab_canceled, bg=DARK_BG)
        can_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.list_canceled = tk.Listbox(can_frame, height=18)
        self.list_canceled.pack(side="left", fill="both", expand=True)

        sb2 = tk.Scrollbar(can_frame, orient="vertical", command=self.list_canceled.yview)
        sb2.pack(side="right", fill="y")
        self.list_canceled.config(yscrollcommand=sb2.set)

        # Buttons
        btns = tk.Frame(body, bg=DARK_BG)
        btns.pack(fill="x", pady=(12, 0))

        tk.Button(
            btns, text="Rafraîchir", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.refresh
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_cancel = tk.Button(
            btns, text="Annuler le RDV (à venir)", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.cancel_selected_upcoming
        )
        self.btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            btns, text="Retour", bg=BTN_BG, fg=BTN_FG, height=2,
            command=self.back
        ).pack(side="left", fill="x", expand=True)

        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._on_tab_changed()

    def _on_tab_changed(self, _evt=None):
        tab_text = self.nb.tab(self.nb.select(), "text")
        # Cancel only allowed in "À venir"
        self.btn_cancel.config(state=("normal" if tab_text == "À venir" else "disabled"))

    def refresh(self):
        self.list_upcoming.delete(0, tk.END)
        self.list_canceled.delete(0, tk.END)
        self._upcoming = []
        self._canceled = []

        upcoming = list(self.service.list_patient_rdvs_upcoming(self.user["id"]))
        canceled = list(self.service.list_patient_rdvs_canceled(self.user["id"]))

        self._upcoming = upcoming
        self._canceled = canceled

        # Fill upcoming
        if not upcoming:
            self.list_upcoming.insert(tk.END, "Aucun RDV à venir.")
        else:
            for r in upcoming:
                start_dt = datetime.fromisoformat(r["start"])
                end_dt = datetime.fromisoformat(r["end"])
                date_txt = start_dt.strftime("%d/%m/%Y")
                time_txt = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"
                urgent_txt = " | URGENT" if int(r["is_urgent"]) == 1 else ""
                line = f"{date_txt} {time_txt} | Dr {r['medecin_name']}{urgent_txt}"
                self.list_upcoming.insert(tk.END, line)

        # Fill canceled
        if not canceled:
            self.list_canceled.insert(tk.END, "Aucun RDV annulé.")
        else:
            for r in canceled:
                start_dt = datetime.fromisoformat(r["start"])
                end_dt = datetime.fromisoformat(r["end"])
                date_txt = start_dt.strftime("%d/%m/%Y")
                time_txt = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"
                urgent_txt = " | URGENT" if int(r["is_urgent"]) == 1 else ""
                line = f"{date_txt} {time_txt} | Dr {r['medecin_name']}{urgent_txt}"
                self.list_canceled.insert(tk.END, line)

        self.summary.config(
            text=f"À venir: {len(upcoming)} | Annulés: {len(canceled)}"
        )
        self._on_tab_changed()

    def cancel_selected_upcoming(self):
        if not self._upcoming:
            messagebox.showinfo("Info", "Aucun RDV à annuler.")
            return

        idxs = self.list_upcoming.curselection()
        if not idxs:
            messagebox.showwarning("Info", "Sélectionnez un RDV à venir.")
            return

        idx = int(idxs[0])
        if idx >= len(self._upcoming):
            return

        rdv = self._upcoming[idx]
        start_dt = datetime.fromisoformat(rdv["start"])
        if start_dt <= datetime.now():
            messagebox.showerror("Erreur", "Impossible: RDV déjà passé.")
            return

        if not messagebox.askyesno("Confirmation", "Annuler ce rendez-vous ?"):
            return

        ok = self.service.cancel_rdv(int(rdv["id"]))
        if not ok:
            messagebox.showerror("Erreur", "Annulation impossible.")
            return

        messagebox.showinfo("OK", "Rendez-vous annulé.")
        self.refresh()

        # refresh reminder card in PatientHome if available
        if hasattr(self.parent, "refresh_reminder"):
            try:
                self.parent.refresh_reminder()
            except Exception:
                pass

    def back(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()