from __future__ import annotations

from tkinter import ttk
from app.ui.views.base_view import BaseView


class CartView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Cart",
            subtitle="Stage 1: UI shell. Stage 3 will show real cart + checkout.",
        )

        ttk.Label(self.content, text="Cart is empty (stub).").pack(anchor="nw", pady=6)

        btns = ttk.Frame(self.content)
        btns.pack(anchor="nw", pady=10)

        ttk.Button(btns, text="Proceed to Checkout (stub)", command=self._checkout_stub).pack(side="left")
        ttk.Button(btns, text="Go to Orders", command=lambda: self.on_navigate("orders")).pack(side="left", padx=8)

    def _checkout_stub(self):
        self.set_status("Checkout stub: will create order in Stage 3")
