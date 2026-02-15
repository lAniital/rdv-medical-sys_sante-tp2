import tkinter as tk
from ui.theme import apply_dark, make_btn, make_label, FONT_TITLE

class MedecinAgenda:
    def __init__(self, user, service, parent=None):
        self.user = user
        self.service = service

        self.win = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.win.title("Mon agenda")
        self.win.geometry("760x420")
        self.win.resizable(False, False)
        apply_dark(self.win)

        frame = tk.Frame(self.win, bg="#1f1f1f")
        frame.pack(expand=True, fill="both", padx=20, pady=15)

        make_label(frame, "Agenda (RDV à venir)", font=FONT_TITLE).pack(anchor="w", pady=(0, 12))

        self.listbox = tk.Listbox(frame, height=14)
        self.listbox.pack(fill="both", expand=True)

        make_btn(frame, "Rafraîchir", self.refresh, width=22).pack(pady=10)
        make_btn(frame, "Retour", self.win.destroy, width=22).pack()

        self.refresh()

    def refresh(self):
        self.listbox.delete(0, tk.END)
        rows = self.service.list_doctor_agenda(self.user["id"], include_canceled=False)
        if not rows:
            self.listbox.insert(tk.END, "Aucun RDV.")
            return
        for r in rows:
            urgent = "PRIO" if r["is_urgent"] else "-"
            label = f"RDV#{r['id']} | {r['start']} -> {r['end']} | patient={r['patient_name']} | {urgent}"
            self.listbox.insert(tk.END, label)
