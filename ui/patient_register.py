# ui/patient_register.py - Interface d'inscription pour les patients (appelée depuis login_view)
import tkinter as tk
from tkinter import messagebox

from ui.theme import apply_theme, make_label, make_entry, make_btn, FONT_TITLE


class PatientRegister:
    def __init__(self, auth_service, parent, on_success=None):
        self.auth = auth_service
        self.on_success = on_success

        self.win = tk.Toplevel(parent)
        self.win.title("Créer un compte - PATIENT")

        # FIX: allow resizing + safe size
        self.win.geometry("820x520")
        self.win.minsize(650, 420)
        self.win.resizable(True, True)

        apply_theme(self.win)

        frame = tk.Frame(self.win, bg=self.win["bg"])
        frame.pack(expand=True, fill="both", padx=20, pady=15)

        make_label(frame, "Créer un compte PATIENT", font=FONT_TITLE).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        make_label(frame, "Nom d'utilisateur :").grid(row=1, column=0, sticky="w", pady=6)
        self.username = make_entry(frame)
        self.username.grid(row=1, column=1, sticky="ew", pady=6)

        make_label(frame, "Email :").grid(row=2, column=0, sticky="w", pady=6)
        self.email = make_entry(frame)
        self.email.grid(row=2, column=1, sticky="ew", pady=6)

        make_label(frame, "Mot de passe :").grid(row=3, column=0, sticky="w", pady=6)
        self.password = make_entry(frame, show="*")
        self.password.grid(row=3, column=1, sticky="ew", pady=6)

        make_label(frame, "Confirmer :").grid(row=4, column=0, sticky="w", pady=6)
        self.password2 = make_entry(frame, show="*")
        self.password2.grid(row=4, column=1, sticky="ew", pady=6)

        frame.grid_columnconfigure(1, weight=1)

        make_btn(frame, "Créer mon compte", command=self.create).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(14, 8)
        )
        make_btn(frame, "Retour", command=self.win.destroy).grid(
            row=6, column=0, columnspan=2, sticky="ew"
        )

        # OPTIONAL: auto-fit to content (helps with Windows scaling)
        self.win.update_idletasks()
        w = max(self.win.winfo_reqwidth(), 650)
        h = max(self.win.winfo_reqheight(), 420)
        self.win.geometry(f"{w}x{h}")

        self.username.focus_set()

    def create(self):
        u = self.username.get().strip()
        e = self.email.get().strip()
        p1 = self.password.get().strip()
        p2 = self.password2.get().strip()

        if not u or not e or not p1 or not p2:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs.")
            return
        if p1 != p2:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas.")
            return

        ok, msg = self.auth.create_patient(u, p1, e)
        if not ok:
            messagebox.showerror("Erreur", msg)
            return

        messagebox.showinfo("OK", msg)
        if self.on_success:
            self.on_success()
        self.win.destroy()