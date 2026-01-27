from __future__ import annotations

from tkinter import ttk, messagebox

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class FavoritesView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Favorites",
        )
        self.state = state

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Open Item", command=self.open_item).pack(side="left", padx=8)
        ttk.Button(top, text="Remove", command=self.remove_selected).pack(side="left", padx=8)

        self.tree = ttk.Treeview(self.content, columns=("name", "price"), show="headings", height=14)
        self.tree.heading("name", text="Item")
        self.tree.heading("price", text="Price (EUR)")
        self.tree.column("name", width=520, stretch=True)
        self.tree.column("price", width=120, stretch=False, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=10)

        self.tree.bind("<Double-1>", lambda _e: self.open_item())

    def on_show(self):
        self.refresh()

    def _selected_item_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            return None

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self.state.is_logged_in:
            self.set_status("Please login first")
            return
        if self.state.role != "CUSTOMER":
            self.set_status("Favorites are available for customers")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_list_favorites(user_id)
        if not result.ok:
            self.set_status(result.error.message)
            return

        favs = result.data or []
        if not favs:
            self.set_status("No favorites yet")
            return

        for it in favs:
            self.tree.insert("", "end", iid=str(it["id"]), values=(it["name"], f'{it["price"]:.2f}'))

        self.set_status(f"Loaded {len(favs)} favorites")

    def open_item(self):
        item_id = self._selected_item_id()
        if not item_id:
            self.set_status("Select an item first")
            return
        self.state.select_item(item_id)
        self.on_navigate("item_details")

    def remove_selected(self):
        item_id = self._selected_item_id()
        if not item_id:
            self.set_status("Select an item first")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_remove_favorite(user_id, item_id)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.set_status("Removed from favorites")
        messagebox.showinfo("Favorites", "Removed from favorites.")
        self.refresh()
