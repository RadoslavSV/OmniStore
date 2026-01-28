import tkinter as tk
from tkinter import ttk

from app.db.schema import init_db
from app.db.seed import seed_demo_data_if_empty
from app.ui.main_window import MainWindow


def setup_style(root: tk.Tk) -> None:
    style = ttk.Style(root)

    # ✅ Theme that actually respects colors on Windows
    style.theme_use("clam")

    # ---- Base colors ----
    BG_MAIN = "#EAF2FB"         # very light blue
    BG_PANEL = "#D6E4F5"        # light blue panel
    BG_BUTTON = "#C5DBF2"       # button light blue
    BG_BUTTON_ACTIVE = "#9BBCE3"  # hover/active
    BORDER = "#7AA2D6"
    TEXT_MAIN = "#1F2D3D"
    TEXT_MUTED = "#5C6F82"

    # ---- Root ----
    root.configure(background=BG_MAIN)

    # Apply a default background to all ttk widgets (the "." style)
    style.configure(".", background=BG_PANEL, foreground=TEXT_MAIN)

    # ---- Frames ----
    style.configure("TFrame", background=BG_PANEL)

    # ---- Labels ----
    style.configure("TLabel", background=BG_PANEL, foreground=TEXT_MAIN)

    style.configure("Muted.TLabel", background=BG_PANEL, foreground=TEXT_MUTED)

    style.configure(
        "Title.TLabel",
        background=BG_PANEL,
        foreground=TEXT_MAIN,
        font=("Segoe UI", 16, "bold"),
    )

    # ---- Buttons ----
    style.configure(
        "TButton",
        background=BG_BUTTON,
        foreground=TEXT_MAIN,
        padding=8,
        relief="flat",
        borderwidth=1,
    )
    style.map(
        "TButton",
        background=[("active", BG_BUTTON_ACTIVE), ("pressed", BG_BUTTON_ACTIVE)],
        foreground=[("disabled", TEXT_MUTED)],
    )

    # ---- Treeview ----
    style.configure(
        "Treeview",
        background="white",
        fieldbackground="white",
        foreground=TEXT_MAIN,
        rowheight=24,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
    )
    style.configure(
        "Treeview.Heading",
        background=BG_PANEL,
        foreground=TEXT_MAIN,
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", BG_BUTTON_ACTIVE)],
    )

    # ---- Separator ----
    style.configure("TSeparator", background=BORDER)

    # ---- Optional: Entry / Combobox polish ----
    style.configure("TEntry", padding=4)
    style.configure("TCombobox", padding=4)


def run_app():
    init_db()
    seed_demo_data_if_empty()

    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
