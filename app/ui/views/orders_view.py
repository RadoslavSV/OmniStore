from __future__ import annotations

from tkinter import ttk
from app.ui.views.base_view import BaseView


class OrdersView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Orders",
            subtitle="Stage 2.1: visible only for customers. Stage 3 will load orders from backend.",
        )
        self.state = state

        ttk.Button(self.content, text="Refresh (stub)", command=self._refresh_stub).pack(anchor="nw")

        self.tree = ttk.Treeview(self.content, columns=("status", "total"), show="headings", height=10)
        self.tree.heading("status", text="Status")
        self.tree.heading("total", text="Total (EUR)")
        self.tree.pack(fill="x", pady=10)

        self.tree.insert("", "end", values=("CREATED", "380.00"))
        ttk.Button(self.content, text="Back to Catalog", command=lambda: self.on_navigate("catalog")).pack(anchor="nw")

    def _refresh_stub(self):
        self.set_status(f"Orders refreshed (stub). Role: {self.state.role}")
