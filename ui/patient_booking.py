# ui/patient_booking.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date
import calendar

from data.db import Database
from services.rdv_service import RDVService
from ui.theme import apply_theme


DARK_BG = "#1f1f1f"
DARK_FG = "#ffffff"
BTN_BG = "#e6e6e6"
BTN_FG = "#000000"
SELECT_BG = "#4CAF50"  # highlight for selected slot


class PatientBookingWindow:
    """
    Booking flow:
    1) Choose doctor
    2) Choose date (calendar)  -> past days disabled
    3) Click "Afficher les créneaux"
    4) Pick an hour button     -> past slots disabled + selected highlighted
    5) Confirm booking (+ urgent option)
    """

    def __init__(self, user: dict, parent: tk.Tk | tk.Toplevel):
        self.user = user
        self.parent = parent

        self.db = Database()
        self.service = RDVService(self.db)

        self.win = tk.Toplevel(parent)
        apply_theme(self.win)
        self.win.title("Prendre un rendez-vous")
        self.win.geometry("900x520")
        self.win.configure(bg=DARK_BG)
        self.win.protocol("WM_DELETE_WINDOW", self.back)

        # state
        self._medecins = []
        self.selected_medecin_id = None
        self.selected_date = date.today()
        self.selected_creneau_id = None
        self.selected_time_button = None

        # calendar state
        self.cal_year = self.selected_date.year
        self.cal_month = self.selected_date.month

        self._build_ui()
        self.load_medecins()
        self.render_calendar()

    # ---------------- UI ----------------

    def _build_ui(self):
        top = tk.Frame(self.win, bg=DARK_BG)
        top.pack(fill="x", padx=16, pady=10)

        title = tk.Label(
            top,
            text="Prendre un rendez-vous",
            bg=DARK_BG,
            fg=DARK_FG,
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w")

        main = tk.Frame(self.win, bg=DARK_BG)
        main.pack(fill="both", expand=True, padx=16, pady=10)

        # left: doctor
        left = tk.Frame(main, bg=DARK_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        tk.Label(left, text="Choisissez un médecin :", bg=DARK_BG, fg=DARK_FG).pack(anchor="w")
        self.med_list = tk.Listbox(left, width=35, height=14)
        self.med_list.pack(fill="both", expand=False, pady=(6, 10))
        self.med_list.bind("<<ListboxSelect>>", self.on_select_medecin)

        self.btn_reload_med = tk.Button(
            left, text="Charger médecins", bg=BTN_BG, fg=BTN_FG, height=2, command=self.load_medecins
        )
        self.btn_reload_med.pack(fill="x", pady=(0, 8))

        # middle: calendar
        mid = tk.Frame(main, bg=DARK_BG)
        mid.grid(row=0, column=1, sticky="nsew", padx=(0, 14))

        tk.Label(mid, text="Choisissez la date :", bg=DARK_BG, fg=DARK_FG).pack(anchor="w")
        self.cal_frame = tk.Frame(mid, bg=DARK_BG, bd=1, relief="solid")
        self.cal_frame.pack(fill="x", pady=(6, 10))

        cal_nav = tk.Frame(mid, bg=DARK_BG)
        cal_nav.pack(fill="x", pady=(0, 10))

        tk.Button(cal_nav, text="◀", width=5, bg=BTN_BG, fg=BTN_FG, command=self.prev_month).pack(side="left")
        self.lbl_month = tk.Label(cal_nav, text="", bg=DARK_BG, fg=DARK_FG, font=("Segoe UI", 11, "bold"))
        self.lbl_month.pack(side="left", expand=True)
        tk.Button(cal_nav, text="▶", width=5, bg=BTN_BG, fg=BTN_FG, command=self.next_month).pack(side="right")

        self.btn_show_slots = tk.Button(
            mid, text="Afficher les créneaux", bg=BTN_BG, fg=BTN_FG, height=2, command=self.load_slots_for_selection
        )
        self.btn_show_slots.pack(fill="x")

        # right: time slots + urgent + confirm
        right = tk.Frame(main, bg=DARK_BG)
        right.grid(row=0, column=2, sticky="nsew")

        tk.Label(right, text="Créneaux disponibles :", bg=DARK_BG, fg=DARK_FG).pack(anchor="w")

        self.times_frame = tk.Frame(right, bg=DARK_BG)
        self.times_frame.pack(fill="x", pady=(6, 12))

        self.urgent_var = tk.IntVar(value=0)
        tk.Checkbutton(
            right,
            text="RDV urgent (prioritaire)",
            variable=self.urgent_var,
            bg=DARK_BG,
            fg=DARK_FG,
            selectcolor=DARK_BG,
            activebackground=DARK_BG,
            activeforeground=DARK_FG,
            command=self.on_toggle_urgent,
        ).pack(anchor="w")

        tk.Label(right, text="Motif urgence :", bg=DARK_BG, fg=DARK_FG).pack(anchor="w", pady=(8, 0))
        self.reason_entry = tk.Entry(right, width=35)
        self.reason_entry.pack(fill="x", pady=(4, 10))
        self.reason_entry.configure(state="disabled")

        self.btn_confirm = tk.Button(
            right, text="Confirmer le rendez-vous", bg=BTN_BG, fg=BTN_FG, height=2, command=self.confirm_booking
        )
        self.btn_confirm.pack(fill="x", pady=(0, 10))

        self.btn_back = tk.Button(right, text="Retour", bg=BTN_BG, fg=BTN_FG, height=2, command=self.back)
        self.btn_back.pack(fill="x")

        # layout weights
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_columnconfigure(2, weight=1)

    def _build_slot_group(self, parent: tk.Frame, title: str):
        group = tk.Frame(parent, bg=DARK_BG, bd=1, relief="solid")
        tk.Label(
            group,
            text=title,
            bg=DARK_BG,
            fg=DARK_FG,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=8, pady=(6, 2))
        grid = tk.Frame(group, bg=DARK_BG)
        grid.pack(fill="x", padx=8, pady=(2, 8))
        group.pack(fill="x", pady=(0, 10))
        return grid

    # ---------------- Doctor list ----------------

    def load_medecins(self):
        self.med_list.delete(0, tk.END)
        self._medecins = list(self.service.list_medecins())
        for m in self._medecins:
            label = f"{m['id']} - Dr {m['username']} ({m['speciality'] or '---'})"
            self.med_list.insert(tk.END, label)

        self.selected_medecin_id = None
        self.selected_creneau_id = None
        self._clear_times()

    def on_select_medecin(self, _evt=None):
        idxs = self.med_list.curselection()
        if not idxs:
            return
        m = self._medecins[idxs[0]]
        self.selected_medecin_id = m["id"]
        self.selected_creneau_id = None
        self._clear_times()

    # ---------------- Calendar ----------------

    def render_calendar(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()

        today = date.today()
        month_name = calendar.month_name[self.cal_month]
        self.lbl_month.config(text=f"{month_name} {self.cal_year}")

        headers = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
        hdr = tk.Frame(self.cal_frame, bg=DARK_BG)
        hdr.pack(fill="x")
        for h in headers:
            tk.Label(hdr, text=h, width=4, bg=DARK_BG, fg=DARK_FG).pack(side="left")

        cal = calendar.Calendar(firstweekday=0)  # Monday
        weeks = cal.monthdayscalendar(self.cal_year, self.cal_month)

        for week in weeks:
            row = tk.Frame(self.cal_frame, bg=DARK_BG)
            row.pack(fill="x")
            for day_num in week:
                if day_num == 0:
                    tk.Label(row, text=" ", width=4, bg=DARK_BG, fg=DARK_FG).pack(side="left")
                    continue

                day_date = date(self.cal_year, self.cal_month, day_num)
                is_selected = day_date == self.selected_date

                day_btn = tk.Button(
                    row,
                    text=str(day_num),
                    width=4,
                    bg=("#bbbbbb" if is_selected else BTN_BG),
                    fg=BTN_FG,
                    command=lambda dd=day_date: self.select_date(dd),
                )

                # Disable past days
                if day_date < today:
                    day_btn.configure(state="disabled")

                day_btn.pack(side="left")

    def select_date(self, d: date):
        self.selected_date = d
        self.selected_creneau_id = None
        self._clear_times()
        self.render_calendar()

    def prev_month(self):
        today = date.today()
        if self.cal_year == today.year and self.cal_month == today.month:
            return

        self.cal_month -= 1
        if self.cal_month == 0:
            self.cal_month = 12
            self.cal_year -= 1
        self.render_calendar()

    def next_month(self):
        self.cal_month += 1
        if self.cal_month == 13:
            self.cal_month = 1
            self.cal_year += 1
        self.render_calendar()

    # ---------------- Slots / times ----------------

    def load_slots_for_selection(self):
        if not self.selected_medecin_id:
            messagebox.showwarning("Info", "Veuillez sélectionner un médecin.")
            return

        self.selected_creneau_id = None
        self.selected_time_button = None
        self._clear_times()

        slots = list(self.service.list_available_slots_by_date(self.selected_medecin_id, self.selected_date))
        if not slots:
            messagebox.showinfo("Info", "Aucun créneau disponible pour cette date.")
            return

        now = datetime.now()

        # Split into morning / afternoon
        morning = []
        afternoon = []
        for slot in slots:
            start_dt = datetime.fromisoformat(slot["start"])
            if start_dt.hour < 12:
                morning.append(slot)
            else:
                afternoon.append(slot)

        # Create 2 groups
        matin_grid = self._build_slot_group(self.times_frame, "Matin")
        aprem_grid = self._build_slot_group(self.times_frame, "Après-midi")

        def add_buttons(grid_parent: tk.Frame, slot_list: list):
            col = 0
            row = 0
            for slot in slot_list:
                creneau_id = slot["id"]
                start_dt = datetime.fromisoformat(slot["start"])
                label = start_dt.strftime("%H:%M")

                btn = tk.Button(
                    grid_parent,
                    text=label,
                    width=8,
                    bg=BTN_BG,
                    fg=BTN_FG,
                )
                btn.configure(command=lambda cid=creneau_id, b=btn: self.select_slot(cid, b))

                # FIX: disable past slots only when selected day is today, and use <=
                if self.selected_date == date.today() and start_dt <= now:
                    btn.configure(state="disabled")

                btn.grid(row=row, column=col, padx=4, pady=4)

                col += 1
                if col >= 6:
                    col = 0
                    row += 1

        # Fill groups
        if morning:
            add_buttons(matin_grid, morning)
        else:
            tk.Label(matin_grid, text="Aucun créneau", bg=DARK_BG, fg=DARK_FG).grid(row=0, column=0, sticky="w")

        if afternoon:
            add_buttons(aprem_grid, afternoon)
        else:
            tk.Label(aprem_grid, text="Aucun créneau", bg=DARK_BG, fg=DARK_FG).grid(row=0, column=0, sticky="w")

    def select_slot(self, creneau_id: int, button: tk.Button):
        self.selected_creneau_id = creneau_id

        # Reset previous selection
        if self.selected_time_button and self.selected_time_button.winfo_exists():
            self.selected_time_button.configure(bg=BTN_BG, fg=BTN_FG)

        # Highlight new selection (FIX: set fg readable)
        button.configure(bg=SELECT_BG, fg=DARK_FG)
        self.selected_time_button = button

    def _clear_times(self):
        for w in self.times_frame.winfo_children():
            w.destroy()
        self.selected_time_button = None

    # ---------------- Urgent ----------------

    def on_toggle_urgent(self):
        if self.urgent_var.get() == 1:
            self.reason_entry.configure(state="normal")
        else:
            self.reason_entry.delete(0, tk.END)
            self.reason_entry.configure(state="disabled")

    # ---------------- Confirm ----------------

    def confirm_booking(self):
        if not self.selected_medecin_id:
            messagebox.showwarning("Info", "Sélectionnez un médecin.")
            return
        if not self.selected_creneau_id:
            messagebox.showwarning("Info", "Sélectionnez une heure (créneau).")
            return

        is_urgent = self.urgent_var.get() == 1
        reason = self.reason_entry.get().strip() if is_urgent else None

        ok = self.service.book_rdv(
            patient_id=self.user["id"],
            creneau_id=self.selected_creneau_id,
            is_urgent=is_urgent,
            reason=reason,
        )

        if not ok:
            messagebox.showerror("Erreur", "Impossible de réserver ce créneau (déjà pris / motif manquant / erreur).")
            return

        messagebox.showinfo("OK", "Rendez-vous confirmé.")
        if hasattr(self.parent, "refresh_rdvs"):
            self.parent.refresh_rdvs()
        self.selected_creneau_id = None
        self.load_slots_for_selection()

    # ---------------- Back ----------------

    def back(self):
        try:
            if self.win.grab_current():
                self.win.grab_release()
        except Exception:
            pass

        try:
            self.db.close()
        except Exception:
            pass
        self.win.destroy()
