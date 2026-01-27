from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.app_state import AppState
from app.ui.theme import apply_theme

from app.ui.views.login_view import LoginView
from app.ui.views.register_view import RegisterView
from app.ui.views.catalog_view import CatalogView
from app.ui.views.cart_view import CartView
from app.ui.views.orders_view import OrdersView
from app.ui.views.item_details_view import ItemDetailsView
from app.ui.views.favorites_view import FavoritesView
from app.ui.views.history_view import HistoryView

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("OmniStore")
        self.root.minsize(1000, 650)

        apply_theme(self.root)

        self.state = AppState()  # session state (guest by default)

        # Layout
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self.root, style="Sidebar.TFrame")
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ttk.Frame(self.root, style="Content.TFrame")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(1, weight=1)
        self.content.columnconfigure(0, weight=1)

        # Top bar
        self.topbar = ttk.Frame(self.content)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.columnconfigure(0, weight=1)
        self.topbar.columnconfigure(1, weight=0)

        self.status_omnistore = ttk.Label(self.topbar, text="")  # spacer label
        self.ToplevelStatus = tk.StringVar(value="")
        self.status_label = ttk.Label(self.topbar, textvariable=self.ToplevelStatus, style="Muted.TLabel")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.logout_btn = ttk.Button(self.topbar, text="Logout", command=self.logout)
        self.logout_btn.grid(row=0, column=1, sticky="e")

        # Body area for views
        self.body = ttk.Frame(self.content, style="Content.TFrame")
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.rowconfigure(0, weight=1)
        self.body.columnconfigure(0, weight=1)

        # Views
        self.views: dict[str, ttk.Frame] = {}
        self._create_views()

        # Sidebar navigation buttons (kept so we can show/hide)
        self.nav_buttons: dict[str, ttk.Button] = {}

        self._build_sidebar()

        self._refresh_ui_for_state()
        self.show("login")

    # -------- Views --------

    def _create_views(self):
        self.views["login"] = LoginView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state, on_state_changed=self._refresh_ui_for_state)
        self.views["register"] = RegisterView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state, on_state_changed=self._refresh_ui_for_state)
        self.views["catalog"] = CatalogView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state)
        self.views["cart"] = CartView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state)
        self.views["orders"] = OrdersView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state)
        self.views["item_details"] = ItemDetailsView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state)
        self.views["favorites"] = FavoritesView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state)
        self.views["history"] = HistoryView(self.body, on_navigate=self.show, set_status=self.set_status, state=self.state)

        for v in self.views.values():
            v.grid(row=0, column=0, sticky="nsew")

    # -------- Sidebar --------

    def _build_sidebar(self):
        ttk.Label(self.sidebar, text="OmniStore", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))

        # Always visible
        self.nav_buttons["login"] = ttk.Button(self.sidebar, text="Login", style="Nav.TButton", command=lambda: self.show("login"))
        self.nav_buttons["register"] = ttk.Button(self.sidebar, text="Register", style="Nav.TButton", command=lambda: self.show("register"))
        self.nav_buttons["catalog"] = ttk.Button(self.sidebar, text="Catalog", style="Nav.TButton", command=lambda: self.show("catalog"))

        # Requires login
        self.nav_buttons["cart"] = ttk.Button(self.sidebar, text="Cart", style="Nav.TButton", command=lambda: self.show("cart"))
        self.nav_buttons["orders"] = ttk.Button(self.sidebar, text="Orders", style="Nav.TButton", command=lambda: self.show("orders"))
        self.nav_buttons["favorites"] = ttk.Button(self.sidebar, text="Favorites", style="Nav.TButton", command=lambda: self.show("favorites"))
        self.nav_buttons["history"] = ttk.Button(self.sidebar, text="History", style="Nav.TButton", command=lambda: self.show("history"))

        # Lay them out (we'll hide/show with grid_remove)
        row = 1
        for key in ["login", "register", "catalog", "cart", "orders", "favorites", "history"]:
            self.nav_buttons[key].grid(row=row, column=0, sticky="ew", pady=4)
            row += 1

        self.sidebar.rowconfigure(row, weight=1)
        ttk.Label(self.sidebar, text="Stage 2.3", style="Muted.TLabel").grid(row=row + 1, column=0, sticky="w", pady=(10, 0))

    # -------- State / UI refresh --------

    def _refresh_ui_for_state(self):
        """
        Show/hide buttons and update status bar based on AppState.
        """
        role = self.state.role  # GUEST/CUSTOMER/ADMIN
        logged = self.state.is_logged_in

        # Nav visibility
        if not logged:
            self.nav_buttons["cart"].grid_remove()
            self.nav_buttons["orders"].grid_remove()
            self.nav_buttons["login"].grid()
            self.nav_buttons["register"].grid()
        else:
            self.nav_buttons["cart"].grid()
            self.nav_buttons["orders"].grid_remove() if role == "ADMIN" else self.nav_buttons["orders"].grid()
            self.nav_buttons["login"].grid_remove()
            self.nav_buttons["register"].grid_remove()

        # Logout button visibility
        if logged:
            self.logout_btn.grid()
        else:
            self.logout_btn.grid_remove()

        # Status text
        if not logged:
            self.ToplevelStatus.set("Not logged in")
        else:
            s = self.state.session
            self.ToplevelStatus.set(f"Logged in as {s.username} ({s.role}) | Currency: {s.currency}")

    def logout(self):
        self.state.set_guest()
        self._refresh_ui_for_state()
        self.set_status("Logged out")
        self.show("login")

    # -------- Navigation --------

    def show(self, view_key: str):
        view = self.views.get(view_key)
        if view is None:
            return

        # Access control
        if view_key in ("cart", "orders") and not self.state.is_logged_in:
            self.set_status("Please login first")
            self.views["login"].tkraise()
            return

        # Admin rule: in your project, ADMIN is mostly for management; orders are customer feature
        if view_key == "orders" and self.state.role == "ADMIN":
            self.set_status("Orders are available for customers")
            self.views["catalog"].tkraise()
            return

        view.tkraise()

        # Auto refresh if the view supports it
        if hasattr(view, "on_show"):
            try:
                view.on_show()
            except Exception:
                pass

    def set_status(self, text: str):
        # Keep a short UI-friendly status bar message
        if text:
            if self.state.is_logged_in:
                s = self.state.session
                self.ToplevelStatus.set(f"{text} | {s.username} ({s.role}) | {s.currency}")
            else:
                self.ToplevelStatus.set(text)
