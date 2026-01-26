from __future__ import annotations

from tkinter import ttk

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class CatalogView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Catalog",
            subtitle="Stage 2.2: loads real items via StoreAppService (UI-safe).",
        )
        self.state = state

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Go to Cart", command=lambda: self.on_navigate("cart")).pack(side="left", padx=8)

        self.tree = ttk.Treeview(self.content, columns=("name", "price"), show="headings", height=14)
        self.tree.heading("name", text="Item")
        self.tree.heading("price", text="Price (EUR)")
        self.tree.column("name", width=420, stretch=True)
        self.tree.column("price", width=120, stretch=False, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=10)

        # Load once on create
        self.refresh()

    def refresh(self):
        # Clear
        for i in self.tree.get_children():
            self.tree.delete(i)

        # UI-safe call
        result = store_app_service.ui_list_items()

        if not result.ok:
            self.set_status(result.error.message)
            return

        items = result.data or []
        if not items:
            self.set_status("Catalog is empty")
            return

        # result.data already DTO-normalized: {id, name, price, currency}
        for it in items:
            self.tree.insert("", "end", values=(it["name"], f'{it["price"]:.2f}'))
