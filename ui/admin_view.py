# ui/admin_view.py - Interface d'administration pour gérer les médecins
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from ui.theme import apply_theme
from data.db import Database
from services.admin_service import AdminService


class AdminView:
    def __init__(self, user: dict, on_logout=None):
        self.user = user
        self.on_logout = on_logout

        self.db = Database()
        self.service = AdminService(self.db)

        self.win = tk.Toplevel()
        apply_theme(self.win)

        self.win.title("Espace Admin")
        self.win.geometry("820x520")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.logout)

        title = tk.Label(self.win, text=f"Bienvenue {user['username']}", font=("Segoe UI", 18, "bold"))
        title.pack(pady=(18, 10))

        main = tk.Frame(self.win)
        main.pack(fill="both", expand=True, padx=18, pady=10)

        # Left: doctor list
        left = tk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tk.Label(left, text="Médecins", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        list_frame = tk.Frame(left)
        list_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.listbox = tk.Listbox(list_frame, height=18)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        btn_row = tk.Frame(left)
        btn_row.pack(fill="x", pady=10)

        self.btn_deactivate = tk.Button(btn_row, text="Désactiver", command=self.deactivate_selected)
        self.btn_deactivate.pack(side="left")

        self.btn_activate = tk.Button(btn_row, text="Réactiver", command=self.activate_selected)
        self.btn_activate.pack(side="left", padx=10)

        self.btn_refresh = tk.Button(btn_row, text="Rafraîchir", command=self.refresh_doctors)
        self.btn_refresh.pack(side="left")

        # Right: add doctor form
        right = tk.Frame(main)
        right.pack(side="right", fill="y")

        tk.Label(right, text="Ajouter un médecin", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        form = tk.Frame(right)
        form.pack(fill="x", pady=(8, 0))

        tk.Label(form, text="Username").grid(row=0, column=0, sticky="w", pady=4)
        self.e_username = tk.Entry(form, width=28)
        self.e_username.grid(row=0, column=1, pady=4)

        tk.Label(form, text="Password").grid(row=1, column=0, sticky="w", pady=4)
        self.e_password = tk.Entry(form, width=28, show="*")
        self.e_password.grid(row=1, column=1, pady=4)

        tk.Label(form, text="Email").grid(row=2, column=0, sticky="w", pady=4)
        self.e_email = tk.Entry(form, width=28)
        self.e_email.grid(row=2, column=1, pady=4)

        # ---- Speciality search + quick select (Combobox) ----
        tk.Label(form, text="Rechercher spécialité").grid(row=3, column=0, sticky="w", pady=4)

        self.all_specialities = list(self.service.list_specialities())
        self.spec_var = tk.StringVar(value="")

        self.cb_speciality = ttk.Combobox(
            form,
            textvariable=self.spec_var,
            values=self.all_specialities,
            width=26,
            state="normal",  # allow typing
        )
        self.cb_speciality.grid(row=3, column=1, pady=4, sticky="ew")

        # When user selects from dropdown -> fill "Spécialité"
        self.cb_speciality.bind("<<ComboboxSelected>>", self.on_speciality_selected)

        # When user types -> filter values + auto-open dropdown
        self.cb_speciality.bind("<KeyRelease>", self.on_speciality_type)

        tk.Label(form, text="Spécialité").grid(row=4, column=0, sticky="w", pady=4)
        self.e_speciality = tk.Entry(form, width=28)
        self.e_speciality.grid(row=4, column=1, pady=4)

        form.grid_columnconfigure(1, weight=1)

        tk.Button(right, text="Ajouter", width=26, command=self.add_doctor).pack(pady=(12, 0))

        tk.Label(
            right,
            text="Note: Désactiver = le médecin ne sera plus visible\npour les patients, mais l’historique reste.",
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        # Bottom logout
        tk.Button(self.win, text="Se déconnecter", width=30, height=2, command=self.logout).pack(pady=(10, 18))

        self._doctors = []
        self.refresh_doctors()

    # ----------- Speciality combobox behavior -----------

    def on_speciality_selected(self, _evt=None):
        val = (self.spec_var.get() or "").strip()
        if val:
            self.e_speciality.delete(0, tk.END)
            self.e_speciality.insert(0, val)

    def on_speciality_type(self, _evt=None):
        typed = (self.spec_var.get() or "").strip().lower()

        if not typed:
            filtered = self.all_specialities
        else:
            filtered = [s for s in self.all_specialities if typed in (s or "").lower()]

        self.cb_speciality["values"] = filtered

        # Auto-open dropdown so user sees results immediately (no click needed)
        if filtered:
            try:
                self.cb_speciality.event_generate("<Down>")
            except Exception:
                pass

    # ----------- Doctors list -----------

    def refresh_doctors(self):
        self.listbox.delete(0, tk.END)
        self._doctors = list(self.service.list_doctors(include_inactive=True))

        for d in self._doctors:
            active_txt = "ACTIF" if int(d["active"]) == 1 else "INACTIF"
            spec = d["speciality"] or "-"
            email = d["email"] or "-"
            line = f"{active_txt} | Dr {d['username']} | {spec} | {email}"
            self.listbox.insert(tk.END, line)

    def _get_selected_doctor(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self._doctors[int(sel[0])]

    # ----------- Actions -----------

    def add_doctor(self):
        ok, msg = self.service.create_doctor(
            self.e_username.get(),
            self.e_password.get(),
            self.e_email.get(),
            self.e_speciality.get(),
        )
        if not ok:
            messagebox.showerror("Erreur", msg)
            return

        messagebox.showinfo("OK", msg)
        self.e_username.delete(0, tk.END)
        self.e_password.delete(0, tk.END)
        self.e_email.delete(0, tk.END)
        self.e_speciality.delete(0, tk.END)
        self.spec_var.set("")  # clear search box
        self.refresh_doctors()

    def deactivate_selected(self):
        d = self._get_selected_doctor()
        if not d:
            messagebox.showerror("Erreur", "Sélectionnez un médecin.")
            return

        if int(d["active"]) == 0:
            messagebox.showinfo("Info", "Ce médecin est déjà inactif.")
            return

        if not messagebox.askyesno("Confirmer", f"Désactiver Dr {d['username']} ?"):
            return

        if self.service.deactivate_doctor(int(d["id"])):
            self.refresh_doctors()
        else:
            messagebox.showerror("Erreur", "Impossible de désactiver ce médecin.")

    def activate_selected(self):
        d = self._get_selected_doctor()
        if not d:
            messagebox.showerror("Erreur", "Sélectionnez un médecin.")
            return

        if int(d["active"]) == 1:
            messagebox.showinfo("Info", "Ce médecin est déjà actif.")
            return

        if not messagebox.askyesno("Confirmer", f"Réactiver Dr {d['username']} ?"):
            return

        if self.service.reactivate_doctor(int(d["id"])):
            self.refresh_doctors()
        else:
            messagebox.showerror("Erreur", "Impossible de réactiver ce médecin.")

    def logout(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()
        if self.on_logout:
            self.on_logout()