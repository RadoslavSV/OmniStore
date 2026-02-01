from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class CatalogView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Catalog",
        )
        self.state = state
        self.items_index = {}  # item_id -> dto

        # --- Categories filter state ---
        self._categories: list[dict] = []  # [{"id":..,"name":..}]
        self._cat_vars: dict[int, tk.BooleanVar] = {}  # cat_id -> var
        self._cat_menu: tk.Menu | None = None

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="View Details", command=self.open_details).pack(side="left", padx=8)
        ttk.Button(top, text="Add to Cart", command=self.add_selected_to_cart).pack(side="left", padx=8)
        ttk.Button(top, text="Go to Cart", command=lambda: self.on_navigate("cart")).pack(side="left", padx=8)
        ttk.Button(top, text="Add to Favorites", command=self.add_selected_to_favorites).pack(side="left", padx=8)

        # Categories dropdown (checkboxes)
        self.btn_categories = ttk.Menubutton(top, text="Categories ▾")
        self.btn_categories.pack(side="left", padx=8)

        self.tree = ttk.Treeview(self.content, columns=("name", "price"), show="headings", height=14)
        self.tree.heading("name", text="Item")
        self.tree.heading("price", text="Price (EUR)")
        self.tree.column("name", width=520, stretch=True)
        self.tree.column("price", width=140, stretch=False, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=10)

        self.tree.bind("<Double-1>", lambda _e: self.open_details())

        # init categories + load items
        self._load_categories()
        self.refresh()

    def on_show(self):
        # Re-load categories (in case admin changed them) and refresh list
        self._load_categories()
        self.refresh()

    def _display_currency(self) -> str:
        if not self.state.is_logged_in or not getattr(self.state, "session", None):
            return "EUR"
        c = getattr(self.state.session, "currency", None) or "EUR"
        return str(c).upper()

    # ---------------- Categories filter ----------------

    def _load_categories(self):
        """
        Loads all categories and rebuilds the checkbox menu.
        Default: all categories checked.
        Keeps previous selections when possible.
        """
        # Remember previous selection
        prev_selected = set(self._selected_category_ids())

        res = store_app_service.ui_list_categories()
        if not res.ok:
            self.set_status(res.error.message)
            self._categories = []
        else:
            self._categories = res.data or []

        # rebuild vars/menu
        self._cat_vars.clear()

        menu = tk.Menu(self.btn_categories, tearoff=0)

        def set_all(value: bool):
            for v in self._cat_vars.values():
                v.set(value)
            self._update_categories_button_text()
            self.refresh()

        # actions
        menu.add_command(label="Select all", command=lambda: set_all(True))
        menu.add_command(label="Clear all", command=lambda: set_all(False))
        menu.add_separator()

        for c in self._categories:
            cid = int(c["id"])
            name = str(c["name"])

            var = tk.BooleanVar(value=True)
            # try restore previous selection (if we had it)
            if prev_selected:
                var.set(cid in prev_selected)

            self._cat_vars[cid] = var

            # when toggled -> refresh
            menu.add_checkbutton(
                label=name,
                variable=var,
                command=self._on_categories_changed,
            )

        self._cat_menu = menu
        self.btn_categories["menu"] = menu
        self._update_categories_button_text()

    def _selected_category_ids(self) -> list[int]:
        out = []
        for cid, var in self._cat_vars.items():
            try:
                if bool(var.get()):
                    out.append(int(cid))
            except Exception:
                pass
        return out

    def _on_categories_changed(self):
        self._update_categories_button_text()
        self.refresh()

    def _update_categories_button_text(self):
        total = len(self._cat_vars)
        selected = len(self._selected_category_ids())

        if total == 0:
            self.btn_categories.config(text="Categories ▾")
            return

        if selected == 0:
            self.btn_categories.config(text="Categories (none)")
        elif selected == total:
            self.btn_categories.config(text="Categories (all)")
        else:
            self.btn_categories.config(text=f"Categories ({selected}/{total})")

    # ---------------- Catalog list ----------------

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.items_index.clear()

        currency = self._display_currency()
        self.tree.heading("price", text=f"Price ({currency})")

        selected_cat_ids = self._selected_category_ids()

        # If no categories selected -> show nothing (user asked "only checked categories")
        # You can change this behavior if you prefer "no selection = all".
        if self._cat_vars and len(selected_cat_ids) == 0:
            self.set_status("No categories selected")
            return

        # IMPORTANT:
        # Use filtered call when we have categories; otherwise default list
        if self._cat_vars:
            result = store_app_service.ui_list_items_filtered(display_currency=currency, category_ids=selected_cat_ids)
        else:
            result = store_app_service.ui_list_items(display_currency=currency)

        if not result.ok:
            self.set_status(result.error.message)
            return

        items = result.data or []
        if not items:
            self.set_status("No items for selected categories" if self._cat_vars else "Catalog is empty")
            return

        for it in items:
            item_id = int(it["id"])
            self.items_index[item_id] = it
            self.tree.insert(
                "",
                "end",
                iid=str(item_id),
                values=(it["name"], f'{float(it["price"]):.2f}'),
            )

        self.set_status(f"Loaded {len(items)} items")

    # ---------------- Actions ----------------

    def _selected_item_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            return None

    def open_details(self):
        item_id = self._selected_item_id()
        if not item_id:
            self.set_status("Select an item first")
            return

        self.state.select_item(item_id)
        self.on_navigate("item_details")

    def add_selected_to_cart(self):
        item_id = self._selected_item_id()
        if not item_id:
            self.set_status("Select an item first")
            return

        if not self.state.is_logged_in:
            self.set_status("Please login first")
            messagebox.showinfo("Login required", "Please login to add items to cart.")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_add_to_cart(user_id, item_id=item_id, quantity=1)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.set_status("Added to cart")
        messagebox.showinfo("Added", "Item added to cart successfully.")

    def add_selected_to_favorites(self):
        item_id = self._selected_item_id()
        if not item_id:
            self.set_status("Select an item first")
            return

        if not self.state.is_logged_in or self.state.role != "CUSTOMER":
            self.set_status("Favorites are available for customers (please login)")
            messagebox.showinfo("Login required", "Please login as customer to use favorites.")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_add_favorite(user_id, item_id)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.set_status("Added to favorites")
        messagebox.showinfo("Favorites", "Added to favorites.")
