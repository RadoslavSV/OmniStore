from __future__ import annotations
import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)

    # Use a native-looking theme on Windows (usually "vista" is best)
    # Fall back gracefully if not available.
    preferred = ["vista", "xpnative", "clam"]
    for t in preferred:
        if t in style.theme_names():
            style.theme_use(t)
            break

    # Small indication of structure (can be expanded later)
    style.configure("Sidebar.TFrame", padding=10)
    style.configure("Content.TFrame", padding=12)

    style.configure("Nav.TButton", padding=(10, 8))
    style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
    style.configure("Muted.TLabel", foreground="#555555")
