import tkinter as tk

class PatientView:
    def __init__(self, user):
        root = tk.Tk()
        root.title("Patient")
        tk.Label(root, text=f"Welcome Patient {user['username']}").pack()
        root.mainloop()
