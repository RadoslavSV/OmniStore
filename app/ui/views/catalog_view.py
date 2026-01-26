from __future__ import annotations

from tkinter import ttk
from app.ui.views.base_view import BaseView


class CatalogView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Catalog",
            subtitle="Stage 2.1: role-aware navigation. Stage 2.2 loads real items.",
        )
        self.state = state

        ttk.Button(self.content, text="Refresh (stub)", command=self._refresh_stub).pack(anchor="nw")

        self.listbox = ttk.Treeview(self.content, columns=("price",), show="headings", height=12)
        self.listbox.heading("price", text="Price (EUR)")
        self.listbox.pack(fill="x", pady=10)

        self._set_dummy_rows()

        ttk.Button(self.content, text="Go to Cart", command=lambda: self.on_navigate("cart")).pack(anchor="nw")

    def _set_dummy_rows(self):
        for i in self.listbox.get_children():
            self.listbox.delete(i)
        self.listbox.insert("", "end", values=("Office Desk - 300.00",))
        self.listbox.insert("", "end", values=("Desk Lamp - 40.00",))

    def _refresh_stub(self):
        self.set_status(f"Catalog refreshed (stub). Currency: {self.state.currency}")
