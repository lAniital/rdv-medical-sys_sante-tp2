import tkinter as tk
from ui.theme import apply_theme

class MedecinView:
    def __init__(self, user):
        self.win = tk.Toplevel()
        apply_theme(self.win)

        self.win.title("Médecin")
        tk.Label(self.win, text=f"Welcome Dr {user['username']}").pack()
        self.win.mainloop()