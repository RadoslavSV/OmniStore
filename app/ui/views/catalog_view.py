from __future__ import annotations

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
            subtitle="Stage 2.3: select item → details, and add to cart (EUR base).",
        )
        self.state = state
        self.items_index = {}  # item_id -> dto

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="View Details", command=self.open_details).pack(side="left", padx=8)
        ttk.Button(top, text="Add to Cart", command=self.add_selected_to_cart).pack(side="left", padx=8)
        ttk.Button(top, text="Go to Cart", command=lambda: self.on_navigate("cart")).pack(side="left", padx=8)
        ttk.Button(top, text="Add to Favorites", command=self.add_selected_to_favorites).pack(side="left", padx=8)
        ttk.Button(top, text="Favorites", command=lambda: self.on_navigate("favorites")).pack(side="left", padx=8)
        ttk.Button(top, text="History", command=lambda: self.on_navigate("history")).pack(side="left", padx=8)

        self.tree = ttk.Treeview(self.content, columns=("name", "price"), show="headings", height=14)
        self.tree.heading("name", text="Item")
        self.tree.heading("price", text="Price (EUR)")
        self.tree.column("name", width=520, stretch=True)
        self.tree.column("price", width=120, stretch=False, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=10)

        self.tree.bind("<Double-1>", lambda _e: self.open_details())

        self.refresh()

    def on_show(self):
        # optional: keep it fresh
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.items_index.clear()

        result = store_app_service.ui_list_items()
        if not result.ok:
            self.set_status(result.error.message)
            return

        items = result.data or []
        if not items:
            self.set_status("Catalog is empty")
            return

        # DTO: {id, name, price, currency}
        for it in items:
            item_id = int(it["id"])
            self.items_index[item_id] = it
            # use iid = item_id for easy selection
            self.tree.insert("", "end", iid=str(item_id), values=(it["name"], f'{it["price"]:.2f}'))

        self.set_status(f"Loaded {len(items)} items")

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
