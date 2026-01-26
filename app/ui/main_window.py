from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.theme import apply_theme
from app.ui.views.login_view import LoginView
from app.ui.views.register_view import RegisterView
from app.ui.views.catalog_view import CatalogView
from app.ui.views.cart_view import CartView
from app.ui.views.orders_view import OrdersView


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("OmniStore")
        self.root.minsize(1000, 650)

        apply_theme(self.root)

        # Grid layout: 2 columns (sidebar + content), 1 row
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self.root, style="Sidebar.TFrame")
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ttk.Frame(self.root, style="Content.TFrame")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # Top info bar (inside content)
        self.topbar = ttk.Frame(self.content)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Not logged in")
        self.status_label = ttk.Label(self.topbar, textvariable=self.status_var, style="Muted.TLabel")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.body = ttk.Frame(self.content)
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.rowconfigure(0, weight=1)
        self.body.columnconfigure(0, weight=1)

        # Views
        self.views: dict[str, ttk.Frame] = {}
        self._create_views()

        # Sidebar navigation
        self._build_sidebar()

        # Default page
        self.show("login")

    def _create_views(self):
        self.views["login"] = LoginView(self.body, on_navigate=self.show, set_status=self.set_status)
        self.views["register"] = RegisterView(self.body, on_navigate=self.show, set_status=self.set_status)
        self.views["catalog"] = CatalogView(self.body, on_navigate=self.show, set_status=self.set_status)
        self.views["cart"] = CartView(self.body, on_navigate=self.show, set_status=self.set_status)
        self.views["orders"] = OrdersView(self.body, on_navigate=self.show, set_status=self.set_status)

        for v in self.views.values():
            v.grid(row=0, column=0, sticky="nsew")

    def _build_sidebar(self):
        ttk.Label(self.sidebar, text="OmniStore", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))

        buttons = [
            ("Login", "login"),
            ("Register", "register"),
            ("Catalog", "catalog"),
            ("Cart", "cart"),
            ("Orders", "orders"),
        ]

        for i, (title, key) in enumerate(buttons, start=1):
            b = ttk.Button(self.sidebar, text=title, style="Nav.TButton", command=lambda k=key: self.show(k))
            b.grid(row=i, column=0, sticky="ew", pady=4)

        # Expand spacer
        self.sidebar.rowconfigure(len(buttons) + 1, weight=1)

        # Bottom hint
        ttk.Label(self.sidebar, text="Stage 1: UI skeleton", style="Muted.TLabel").grid(
            row=len(buttons) + 2, column=0, sticky="w", pady=(10, 0)
        )

    def show(self, view_key: str):
        view = self.views.get(view_key)
        if view is None:
            return
        view.tkraise()

    def set_status(self, text: str):
        self.status_var.set(text)
