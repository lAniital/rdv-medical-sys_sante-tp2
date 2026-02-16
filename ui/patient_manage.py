import tkinter as tk
from tkinter import messagebox
from datetime import datetime

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
        self.win.geometry("900x560")
        self.win.minsize(780, 480)
        self.win.resizable(True, True)

        # internal state (keep separate lists)
        self._future = []
        self._canceled = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self.win)
        header.pack(fill="x", padx=16, pady=(14, 10))

        tk.Label(header, text="Gérer mes rendez-vous", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        self.summary = tk.Label(header, text="", font=("Segoe UI", 10))
        self.summary.pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.win)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Two columns: future | canceled
        left = tk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = tk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ---- FUTURE ----
        tk.Label(left, text="RDV à venir", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.future_list = self._make_list_with_scroll(left)

        # ---- CANCELED ----
        tk.Label(right, text="RDV annulés", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.cancel_list = self._make_list_with_scroll(right)

        # Buttons row
        btns = tk.Frame(self.win)
        btns.pack(fill="x", padx=16, pady=(0, 16))

        tk.Button(btns, text="Rafraîchir", height=2, command=self.refresh).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        tk.Button(btns, text="Annuler RDV (à venir)", height=2, command=self.cancel_selected_future).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        tk.Button(btns, text="Retour", height=2, command=self.back).pack(
            side="left", fill="x", expand=True
        )

    def _make_list_with_scroll(self, parent: tk.Frame) -> tk.Listbox:
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=(6, 0))

        lb = tk.Listbox(frame)
        lb.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(frame, orient="vertical", command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.config(yscrollcommand=sb.set)

        return lb

    def refresh(self):
        self.future_list.delete(0, tk.END)
        self.cancel_list.delete(0, tk.END)

        all_rdvs = list(self.service.list_patient_rdvs(self.user["id"], include_canceled=True))

        # split
        self._future = [r for r in all_rdvs if r["status"] != "ANNULE"]
        self._canceled = [r for r in all_rdvs if r["status"] == "ANNULE"]

        # sort by start datetime
        self._future.sort(key=lambda r: r["start"])
        self._canceled.sort(key=lambda r: r["start"])

        self.summary.config(
            text=f"Total: {len(all_rdvs)} | À venir: {len(self._future)} | Annulés: {len(self._canceled)}"
        )

        if not self._future:
            self.future_list.insert(tk.END, "Aucun RDV à venir.")
        else:
            for r in self._future:
                self.future_list.insert(tk.END, self._format_line(r, prefix="PREVU"))

        if not self._canceled:
            self.cancel_list.insert(tk.END, "Aucun RDV annulé.")
        else:
            for r in self._canceled:
                self.cancel_list.insert(tk.END, self._format_line(r, prefix="ANNULÉ"))

    def _format_line(self, r: dict, prefix: str) -> str:
        start_dt = datetime.fromisoformat(r["start"])
        end_dt = datetime.fromisoformat(r["end"])
        date_txt = start_dt.strftime("%d/%m/%Y")
        time_txt = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"
        urgent_txt = " (URGENT)" if int(r["is_urgent"]) == 1 else ""
        return f"{prefix} | Dr {r['medecin_name']} | {date_txt} {time_txt}{urgent_txt}"

    def cancel_selected_future(self):
        if not self._future:
            messagebox.showinfo("Info", "Aucun RDV à annuler.")
            return

        idxs = self.future_list.curselection()
        if not idxs:
            messagebox.showinfo("Info", "Sélectionnez un RDV dans la liste 'RDV à venir'.")
            return

        idx = int(idxs[0])
        if idx >= len(self._future):
            return

        r = self._future[idx]

        ok = messagebox.askyesno("Confirmation", "Annuler ce rendez-vous ?")
        if not ok:
            return

        done = self.service.cancel_rdv(r["id"])
        if not done:
            messagebox.showerror("Erreur", "Annulation impossible.")
            return

        self.refresh()

    def back(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()