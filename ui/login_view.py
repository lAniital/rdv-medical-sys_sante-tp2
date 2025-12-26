import tkinter as tk
from services.auth_service import AuthService
from data.db import Database
from ui.patient_view import PatientView
from ui.medecin_view import MedecinView
from ui.admin_view import AdminView

class LoginView:
    def __init__(self, root):
        self.root = root
        self.root.title("Connexion")

        tk.Label(root, text="Username").pack()
        self.username_entry = tk.Entry(root)
        self.username_entry.pack()

        tk.Label(root, text="Password").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        tk.Button(root, text="Login", command=self.login).pack()
        self.msg = tk.Label(root, text="")
        self.msg.pack()

        self.db = Database()
        self.auth = AuthService(self.db)

    def login(self):
        user = self.auth.login(
            self.username_entry.get(),
            self.password_entry.get()
        )

        if not user:
            self.msg.config(text="Invalid credentials", fg="red")
            return

        self.root.destroy()
        role = user["role"]

        if role == "PATIENT":
            PatientView(user)
        elif role == "MEDECIN":
            MedecinView(user)
        elif role == "ADMIN":
            AdminView(user)
