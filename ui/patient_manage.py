import tkinter as tk
from tkinter import messagebox

from data.db import Database
from services.rdv_service import RDVService
from ui.theme import apply_theme


class PatientManageWindow:
    def __init__(self, user: dict, parent: tk.Tk | tk.Toplevel):
        self.user = user
        self.parent = parent

        self.db = Database()
        self.service = RDVService(self.db)

        self.win = tk.Toplevel(parent)
        apply_theme(self.win)
        self.win.title("Gérer mes rendez-vous")
        self.win.geometry("700x420")

        tk.Label(self.win, text="Gérer mes rendez-vous (à compléter)").pack(pady=10)

        self.listbox = tk.Listbox(self.win, width=100, height=12)
        self.listbox.pack(padx=10, pady=10, fill="both", expand=True)

        btns = tk.Frame(self.win)
        btns.pack(pady=10)

        tk.Button(btns, text="Rafraîchir", width=18, command=self.refresh).grid(row=0, column=0, padx=6)
        tk.Button(btns, text="Annuler RDV sélectionné", width=22, command=self.cancel_selected).grid(row=0, column=1, padx=6)
        tk.Button(btns, text="Retour", width=18, command=self.back).grid(row=0, column=2, padx=6)

        self._rdvs = []
        self.refresh()

    def refresh(self):
        self.listbox.delete(0, tk.END)
        self._rdvs = list(self.service.list_patient_rdvs(self.user["id"], include_canceled=True))
        for r in self._rdvs:
            prefix = "❌ ANNULÉ" if r["status"] == "ANNULE" else "✅ PREVU"
            self.listbox.insert(tk.END, f"{prefix} | RDV#{r['id']} | Dr {r['medecin_name']} | {r['start']} → {r['end']}")

    def cancel_selected(self):
        idxs = self.listbox.curselection()
        if not idxs:
            messagebox.showinfo("Info", "Sélectionnez un RDV.")
            return
        r = self._rdvs[idxs[0]]
        ok = self.service.cancel_rdv(r["id"])
        if not ok:
            messagebox.showinfo("Info", "Ce RDV est déjà annulé.")
        self.refresh()

    def back(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()
