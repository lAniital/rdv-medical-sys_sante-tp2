# ui/medecin_create_slots.py
import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta
import calendar

from ui.theme import apply_theme, make_btn, make_label, make_entry, FONT_TITLE


DARK_BG = "#1f1f1f"
DARK_FG = "#ffffff"
BTN_BG = "#e6e6e6"
BTN_FG = "#000000"


class MedecinCreateSlots:
    def __init__(self, user, service, parent=None):
        self.user = user
        self.service = service

        self.win = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.win.title("Créer des créneaux")
        self.win.geometry("820x470")
        self.win.resizable(False, False)
        apply_theme(self.win)

        # state
        self.selected_date = date.today()
        self.cal_year = self.selected_date.year
        self.cal_month = self.selected_date.month

        self._build_ui()
        self.render_calendar()
        self._apply_preset("MATIN")

    # ================= UI =================

    def _build_ui(self):
        root = tk.Frame(self.win, bg=DARK_BG)
        root.pack(expand=True, fill="both", padx=16, pady=12)

        make_label(root, "Créer des créneaux", font=FONT_TITLE).pack(anchor="w", pady=(0, 10))

        main = tk.Frame(root, bg=DARK_BG)
        main.pack(fill="both", expand=True)

        # ---------- LEFT : CALENDAR ----------
        left = tk.Frame(main, bg=DARK_BG)
        left.pack(side="left", fill="y", padx=(0, 18))

        make_label(left, "Choisir une date :").pack(anchor="w")

        nav = tk.Frame(left, bg=DARK_BG)
        nav.pack(fill="x", pady=(8, 6))

        tk.Button(nav, text="◀", width=4, bg=BTN_BG, fg=BTN_FG, command=self.prev_month).pack(side="left")
        self.lbl_month = tk.Label(nav, text="", bg=DARK_BG, fg=DARK_FG, font=("Segoe UI", 11, "bold"))
        self.lbl_month.pack(side="left", expand=True)
        tk.Button(nav, text="▶", width=4, bg=BTN_BG, fg=BTN_FG, command=self.next_month).pack(side="right")

        self.cal_frame = tk.Frame(left, bg=DARK_BG, bd=1, relief="solid")
        self.cal_frame.pack(fill="x")

        self.lbl_selected = tk.Label(
            left,
            text="Date sélectionnée: --",
            bg=DARK_BG,
            fg=DARK_FG,
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_selected.pack(anchor="w", pady=(10, 0))

        # ---------- RIGHT : OPTIONS ----------
        right = tk.Frame(main, bg=DARK_BG)
        right.pack(side="left", fill="both", expand=True)

        make_label(right, "Créneaux :",).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Presets
        self.preset_var = tk.StringVar(value="MATIN")

        presets = tk.Frame(right, bg=DARK_BG)
        presets.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Radiobutton(
            presets, text="Matin", variable=self.preset_var, value="MATIN",
            bg=DARK_BG, fg=DARK_FG, selectcolor=DARK_BG,
            activebackground=DARK_BG, activeforeground=DARK_FG,
            command=self.on_preset_change
        ).pack(side="left", padx=(0, 12))

        tk.Radiobutton(
            presets, text="Après-midi", variable=self.preset_var, value="APREM",
            bg=DARK_BG, fg=DARK_FG, selectcolor=DARK_BG,
            activebackground=DARK_BG, activeforeground=DARK_FG,
            command=self.on_preset_change
        ).pack(side="left", padx=(0, 12))

        tk.Radiobutton(
            presets, text="Personnalisé", variable=self.preset_var, value="CUSTOM",
            bg=DARK_BG, fg=DARK_FG, selectcolor=DARK_BG,
            activebackground=DARK_BG, activeforeground=DARK_FG,
            command=self.on_preset_change
        ).pack(side="left")

        make_label(right, "Début (HH:MM):").grid(row=2, column=0, sticky="w", pady=6)
        self.start = make_entry(right)
        self.start.grid(row=2, column=1, sticky="ew", pady=6)

        make_label(right, "Fin (HH:MM):").grid(row=3, column=0, sticky="w", pady=6)
        self.end = make_entry(right)
        self.end.grid(row=3, column=1, sticky="ew", pady=6)

        make_label(right, "Durée (min):").grid(row=4, column=0, sticky="w", pady=6)
        self.step = make_entry(right)
        self.step.insert(0, "30")
        self.step.grid(row=4, column=1, sticky="ew", pady=6)

        # Checkbox include weekend
        self.include_weekend_var = tk.IntVar(value=0)

        tk.Checkbutton(
            right,
            text="Inclure week-end (sam/dim)",
            variable=self.include_weekend_var,
            bg=DARK_BG,
            fg=DARK_FG,
            selectcolor=DARK_BG,
            activebackground=DARK_BG,
            activeforeground=DARK_FG,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 4))

        right.grid_columnconfigure(1, weight=1)

        make_btn(right, "Créer", self.create, width=26).grid(
            row=6, column=0, columnspan=2, pady=(8, 4), sticky="ew"
        )

        make_btn(right, "Créer semaine", self.create_week, width=26).grid(
            row=7, column=0, columnspan=2, pady=(4, 4), sticky="ew"
        )

        make_btn(right, "Retour", self.win.destroy, width=26).grid(
            row=8, column=0, columnspan=2, pady=(6, 0), sticky="ew"
        )

    # ================= CALENDAR =================

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

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.cal_year, self.cal_month)

        for week in weeks:
            row = tk.Frame(self.cal_frame, bg=DARK_BG)
            row.pack(fill="x")
            for day_num in week:
                if day_num == 0:
                    tk.Label(row, text=" ", width=4, bg=DARK_BG, fg=DARK_FG).pack(side="left")
                    continue

                day_date = date(self.cal_year, self.cal_month, day_num)
                is_selected = (day_date == self.selected_date)

                btn = tk.Button(
                    row,
                    text=str(day_num),
                    width=4,
                    bg=("#bbbbbb" if is_selected else BTN_BG),
                    fg=BTN_FG,
                    command=lambda dd=day_date: self.select_date(dd),
                )

                if day_date < today:
                    btn.configure(state="disabled")

                btn.pack(side="left")

        self.lbl_selected.config(text=f"Date sélectionnée: {self.selected_date.isoformat()}")

    def select_date(self, d: date):
        self.selected_date = d
        self.render_calendar()

    def prev_month(self):
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

    # ================= PRESETS =================

    def on_preset_change(self):
        self._apply_preset(self.preset_var.get())

    def _apply_preset(self, preset: str):
        preset = (preset or "").upper()

        # Presets autofill but entries stay clickable.
        if preset == "MATIN":
            self._set_time_fields("08:30", "12:00", "30", editable=False)
        elif preset == "APREM":
            self._set_time_fields("14:00", "18:00", "30", editable=False)
        else:
            self._set_time_fields("08:30", "12:00", "30", editable=True)

    def _set_time_fields(self, start_val: str, end_val: str, step_val: str, editable: bool):
        # Always keep entries clickable
        self.start.configure(state="normal")
        self.end.configure(state="normal")
        self.step.configure(state="normal")

        self.start.delete(0, tk.END)
        self.start.insert(0, start_val)

        self.end.delete(0, tk.END)
        self.end.insert(0, end_val)

        self.step.delete(0, tk.END)
        self.step.insert(0, step_val)

        # Optional visual hint: grey background for preset mode, white for custom
        bg = "white" if editable else "#f0f0f0"
        try:
            self.start.configure(bg=bg)
            self.end.configure(bg=bg)
            self.step.configure(bg=bg)
        except tk.TclError:
            # Some themes/widgets may not support bg config; safe to ignore
            pass

    # ================= CREATE =================

    def create(self):
        self._create_for_day(self.selected_date)

    def create_week(self):
        include_weekend = (self.include_weekend_var.get() == 1)

        total_created = 0
        current = self.selected_date

        for i in range(7):
            day = current + timedelta(days=i)

            if not include_weekend and day.weekday() >= 5:
                continue

            total_created += self._create_for_day(day, silent=True)

        messagebox.showinfo("Info", f"Créneaux créés: {total_created}")

    def _create_for_day(self, day, silent=False):
        try:
            step_int = int(self.step.get().strip())
            if step_int <= 0:
                raise ValueError("Step must be > 0")

            start_str = self.start.get().strip()
            end_str = self.end.get().strip()

            # Validate HH:MM
            start_dt = datetime.strptime(start_str, "%H:%M")
            end_dt = datetime.strptime(end_str, "%H:%M")

            if end_dt <= start_dt:
                raise ValueError("End must be after start")

        except Exception:
            if not silent:
                messagebox.showerror("Erreur", "Paramètres invalides (format HH:MM ou durée incorrecte).")
            return 0

        created = self.service.create_day_slots(
            medecin_id=self.user["id"],
            date=day.isoformat(),
            start=start_str,
            end=end_str,
            step=step_int,
        )

        if not silent and created <= 0:
            messagebox.showinfo("Info", "Aucun créneau créé.")

        return created
