from __future__ import annotations

from tkinter import ttk

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class CartView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Cart",
        )
        self.state = state

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Proceed to Checkout", command=self.checkout).pack(side="left", padx=8)

        self.tree = ttk.Treeview(self.content, columns=("name", "qty", "unit", "subtotal"), show="headings", height=12)
        self.tree.heading("name", text="Item")
        self.tree.heading("qty", text="Qty")
        self.tree.heading("unit", text="Unit (EUR)")
        self.tree.heading("subtotal", text="Subtotal (EUR)")
        self.tree.column("name", width=360, stretch=True)
        self.tree.column("qty", width=60, stretch=False, anchor="center")
        self.tree.column("unit", width=120, stretch=False, anchor="e")
        self.tree.column("subtotal", width=140, stretch=False, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=10)

        self.total_var = ttk.Label(self.content, text="Total: 0.00 EUR", style="Muted.TLabel")
        self.total_var.pack(anchor="ne")

    def on_show(self):
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self.state.is_logged_in:
            self.set_status("Please login first")
            self.total_var.config(text="Total: 0.00 EUR")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_get_cart(user_id, display_currency="EUR")
        if not result.ok:
            self.set_status(result.error.message)
            return

        cart = result.data or {}
        items = cart.get("items", [])
        total = cart.get("total", {"amount": 0, "currency": "EUR"})

        for it in items:
            self.tree.insert(
                "",
                "end",
                values=(
                    it["name"],
                    it["quantity"],
                    f'{it["unit_price"]:.2f}',
                    f'{it["subtotal"]:.2f}',
                ),
            )

        self.total_var.config(text=f'Total: {total["amount"]:.2f} {total["currency"]}')
        self.set_status("Cart loaded")

    def checkout(self):
        if not self.state.is_logged_in:
            self.set_status("Please login first")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_checkout(user_id)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.set_status(f"Purchase successful (order id: {result.data})")
        self.on_navigate("orders")
