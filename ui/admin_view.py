import tkinter as tk

class AdminView:
    def __init__(self, user):
        root = tk.Tk()
        root.title("Admin")
        tk.Label(root, text=f"Welcome Admin {user['username']}").pack()
        root.mainloop()
