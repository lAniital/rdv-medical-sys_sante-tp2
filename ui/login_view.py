import tkinter as tk
from tkinter import messagebox

from data.db import Database
from services.auth_service import AuthService
from ui.theme import apply_dark, make_btn, make_label, make_entry, FONT_TITLE


class LoginView:
    def __init__(self, role: str):
        self.role = role  # PATIENT / MEDECIN / ADMIN

        self.db = Database()
        self.auth = AuthService(self.db)

        self.root = tk.Tk()
        self.root.title(f"Connexion - {self.role}")
        self.root.geometry("520x260")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_menu)

        apply_dark(self.root)

        frame = tk.Frame(self.root, bg="#1f1f1f")
        frame.pack(expand=True, fill="both", padx=20, pady=15)

        make_label(frame, f"Espace {self.role} — Connexion", font=FONT_TITLE).grid(
            row=0, column=0, columnspan=2, pady=(0, 12), sticky="w"
        )

        make_label(frame, "Nom d'utilisateur :").grid(row=1, column=0, sticky="w", pady=6)
        self.username = make_entry(frame)
        self.username.grid(row=1, column=1, sticky="ew", pady=6)

        make_label(frame, "Mot de passe :").grid(row=2, column=0, sticky="w", pady=6)
        self.password = make_entry(frame, show="*")
        self.password.grid(row=2, column=1, sticky="ew", pady=6)

        frame.grid_columnconfigure(1, weight=1)

        make_btn(frame, "Se connecter", self.on_login, width=26).grid(
            row=3, column=0, columnspan=2, pady=(14, 6), sticky="ew"
        )

        if self.role == "PATIENT":
            make_btn(frame, "Créer un compte", self.open_register_patient, width=26).grid(
                row=4, column=0, columnspan=2, pady=6, sticky="ew"
            )

        make_btn(frame, "Retour", self.back_to_menu, width=26).grid(
            row=5, column=0, columnspan=2, pady=(6, 0), sticky="ew"
        )

        self.username.focus()
        self.root.mainloop()

    def on_login(self):
        username = self.username.get().strip()
        password = self.password.get().strip()

        user = self.auth.login(username, password)
        if not user:
            messagebox.showerror("Erreur", "Identifiants incorrects.")
            return

        if user["role"] != self.role:
            messagebox.showerror("Erreur", f"Ce compte n’est pas un {self.role}.")
            return

        # UPDATED — PATIENT flow: open PatientHome with on_logout callback
        if user["role"] == "PATIENT":
            from ui.patient_home import PatientHome

            # hide login window
            self.root.withdraw()

            def back_to_login():
                self.root.deiconify()

            PatientHome(user, on_logout=back_to_login)
            return

        # Other roles
        try:
            if user["role"] == "MEDECIN":
                from ui.medecin_view import MedecinView
                MedecinView(user)
            elif user["role"] == "ADMIN":
                from ui.admin_view import AdminView
                AdminView(user)

            self.root.withdraw()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Crash after login:\n{e}")

    def open_register_patient(self):
        messagebox.showinfo("Info", "On crée l'écran 'Créer un compte' dans la prochaine étape.")

    def back_to_menu(self):
        try:
            self.db.close()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        from ui.main_menu import MainMenu
        MainMenu()
