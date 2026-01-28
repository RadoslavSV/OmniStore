from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)

    # ✅ On Windows, 'clam' actually respects colors.
    style.theme_use("clam")

    # ---- Palette ----
    BG_MAIN = "#EAF2FB"          # very light blue (window background)
    BG_CONTENT = "#D6E4F5"       # main panels
    BG_SIDEBAR = "#C8DBF2"       # sidebar a bit stronger
    BG_BUTTON = "#B7D0EE"        # buttons
    BG_BUTTON_HOVER = "#9BBCE3"  # hover/pressed
    BG_BUTTON_ACTIVE = "#7AA2D6" # selected nav button (optional)
    BORDER = "#6B95CC"
    TEXT_MAIN = "#1F2D3D"
    TEXT_MUTED = "#4F647A"
    WHITE = "#FFFFFF"

    # ---- Root background ----
    root.configure(background=BG_MAIN)

    # Base style applied to everything (helps a lot)
    style.configure(".", background=BG_CONTENT, foreground=TEXT_MAIN)

    # ---- Frames ----
    style.configure("TFrame", background=BG_CONTENT)
    style.configure("Content.TFrame", background=BG_CONTENT)
    style.configure("Sidebar.TFrame", background=BG_SIDEBAR)

    # ---- Labels ----
    style.configure("TLabel", background=BG_CONTENT, foreground=TEXT_MAIN)
    style.configure("Muted.TLabel", background=BG_CONTENT, foreground=TEXT_MUTED)

    style.configure(
        "Title.TLabel",
        background=BG_SIDEBAR,   # title is in sidebar most of the time
        foreground=TEXT_MAIN,
        font=("Segoe UI", 16, "bold"),
    )

    # If you ever use Title on content area, you can also define a content title:
    style.configure(
        "ContentTitle.TLabel",
        background=BG_CONTENT,
        foreground=TEXT_MAIN,
        font=("Segoe UI", 16, "bold"),
    )

    # ---- Buttons (default) ----
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
        background=[("active", BG_BUTTON_HOVER), ("pressed", BG_BUTTON_HOVER), ("disabled", BG_CONTENT)],
        foreground=[("disabled", TEXT_MUTED)],
    )

    # ---- Nav buttons (sidebar) ----
    style.configure(
        "Nav.TButton",
        background=BG_BUTTON,
        foreground=TEXT_MAIN,
        padding=10,
        relief="flat",
        borderwidth=0,
        anchor="w",
    )
    style.map(
        "Nav.TButton",
        background=[("active", BG_BUTTON_HOVER), ("pressed", BG_BUTTON_HOVER)],
    )

    # Optional: a style for "selected" nav button (if later we mark current view)
    style.configure(
        "NavActive.TButton",
        background=BG_BUTTON_ACTIVE,
        foreground=WHITE,
        padding=10,
        relief="flat",
        borderwidth=0,
        anchor="w",
    )
    style.map(
        "NavActive.TButton",
        background=[("active", BG_BUTTON_ACTIVE), ("pressed", BG_BUTTON_ACTIVE)],
    )

    # ---- Entry / Spinbox / Combobox ----
    style.configure("TEntry", padding=6)
    style.configure("TCombobox", padding=6)

    # ---- Separator ----
    style.configure("TSeparator", background=BORDER)

    # ---- Treeview ----
    style.configure(
        "Treeview",
        background=WHITE,
        fieldbackground=WHITE,
        foreground=TEXT_MAIN,
        rowheight=24,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
    )
    style.configure(
        "Treeview.Heading",
        background=BG_CONTENT,
        foreground=TEXT_MAIN,
        relief="flat",
    )
    style.map("Treeview.Heading", background=[("active", BG_BUTTON_HOVER)])
