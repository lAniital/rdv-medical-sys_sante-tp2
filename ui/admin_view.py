import tkinter as tk
from ui.theme import apply_theme   

class AdminView:
    def __init__(self, user):
        self.win = tk.Toplevel()
        apply_theme(self.win)
        self.title("Admin")
        tk.Label(self.win, text=f"Welcome Admin {user['username']}").pack()
        self.mainloop()
