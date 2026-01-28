from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class BaseView(ttk.Frame):
    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None],
        set_status: Callable[[str], None],
        title: str,
        subtitle: str = "",
    ):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self.set_status = set_status

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(header, text=title, style="ContentTitle.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(header, text=subtitle, style="Muted.TLabel").pack(anchor="w")

        self.content = ttk.Frame(self)
        self.content.pack(fill="both", expand=True)
