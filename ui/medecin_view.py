import tkinter as tk

class MedecinView:
    def __init__(self, user):
        root = tk.Tk()
        root.title("Médecin")
        tk.Label(root, text=f"Welcome Dr {user['username']}").pack()
        root.mainloop()
