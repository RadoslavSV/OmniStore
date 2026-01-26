from __future__ import annotations

from tkinter import ttk

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class OrdersView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Orders",
            subtitle="Stage 2.2: real order history (EUR base).",
        )
        self.state = state

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Back to Catalog", command=lambda: self.on_navigate("catalog")).pack(side="left", padx=8)

        self.tree = ttk.Treeview(self.content, columns=("id", "status", "total"), show="headings", height=12)
        self.tree.heading("id", text="Order ID")
        self.tree.heading("status", text="Status")
        self.tree.heading("total", text="Total (EUR)")
        self.tree.column("id", width=90, stretch=False, anchor="center")
        self.tree.column("status", width=140, stretch=False)
        self.tree.column("total", width=140, stretch=False, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=10)

    def on_show(self):
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self.state.is_logged_in:
            self.set_status("Please login first")
            return

        if self.state.role != "CUSTOMER":
            self.set_status("Orders are available for customers")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_list_orders(user_id, limit=50)
        if not result.ok:
            self.set_status(result.error.message)
            return

        orders = result.data or []
        if not orders:
            self.set_status("No orders yet")
            return

        # DTO from ui_list_orders: order_id, created_at, status, total, currency
        for o in orders:
            self.tree.insert("", "end", values=(o["order_id"], o["status"], f'{o["total"]:.2f}'))

        self.set_status("Orders loaded")
