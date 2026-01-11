import tkinter as tk

BG = "#1f1f1f"
FG = "#ffffff"
BTN_BG = "#e6e6e6"
BTN_FG = "#000000"
ENTRY_BG = "#ffffff"
ENTRY_FG = "#000000"

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_BTN = ("Segoe UI", 11, "bold")


def apply_dark(root: tk.Tk | tk.Toplevel):
    root.configure(bg=BG)


# Alias so other windows can reuse the same dark theme name
def apply_theme(root: tk.Tk | tk.Toplevel):
    apply_dark(root)


def make_btn(parent, text, command, width=28):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=BTN_BG,
        fg=BTN_FG,
        font=FONT_BTN,
        relief="flat",
        height=2,
        width=width,
    )


def make_label(parent, text, font=FONT_NORMAL):
    return tk.Label(parent, text=text, bg=BG, fg=FG, font=font)


def make_entry(parent, show=None, width=28):
    return tk.Entry(
        parent,
        show=show,
        bg=ENTRY_BG,
        fg=ENTRY_FG,
        width=width,
        font=FONT_NORMAL,
    )
