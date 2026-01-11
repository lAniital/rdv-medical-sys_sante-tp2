import tkinter as tk
from ui.theme import apply_dark, make_btn, make_label, FONT_TITLE


class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Système de gestion des rendez-vous médicaux")
        self.root.geometry("520x360")
        self.root.resizable(False, False)

        apply_dark(self.root)

        frame = tk.Frame(self.root, bg="#1f1f1f")
        frame.pack(expand=True)

        make_label(
            frame, "Système de gestion des rendez-vous médicaux", font=FONT_TITLE
        ).pack(pady=(20, 25))

        make_btn(frame, "Espace Patient", lambda: self.open_login("PATIENT")).pack(
            pady=6
        )
        make_btn(frame, "Espace Médecin", lambda: self.open_login("MEDECIN")).pack(
            pady=6
        )
        make_btn(frame, "Espace Administrateur", lambda: self.open_login("ADMIN")).pack(
            pady=6
        )
        make_btn(frame, "Quitter", self.root.destroy).pack(pady=(18, 0))

        self.root.mainloop()

    def open_login(self, role: str):
        self.root.destroy()
        from ui.login_view import LoginView # local import to avoid circular import
        LoginView(role)
