from __future__ import annotations

from tkinter import ttk, messagebox

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class ItemDetailsView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Item Details",
            subtitle="Stage 2.3: view details + add to cart (EUR base).",
        )
        self.state = state
        self.item = None  # will hold DTO dict

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Back to Catalog", command=lambda: self.on_navigate("catalog")).pack(side="left")
        ttk.Button(top, text="View 3D (stub)", command=self._view_3d_stub).pack(side="left", padx=8)

        self.header = ttk.Label(self.content, text="", style="Title.TLabel")
        self.header.pack(anchor="nw", pady=(12, 4))

        self.desc = ttk.Label(self.content, text="", wraplength=700, justify="left")
        self.desc.pack(anchor="nw", pady=(0, 10))

        info = ttk.Frame(self.content)
        info.pack(anchor="nw", fill="x")

        self.dim_var = ttk.Label(info, text="")
        self.dim_var.grid(row=0, column=0, sticky="w", pady=2)

        self.weight_var = ttk.Label(info, text="")
        self.weight_var.grid(row=1, column=0, sticky="w", pady=2)

        self.price_var = ttk.Label(info, text="")
        self.price_var.grid(row=2, column=0, sticky="w", pady=2)

        self.cat_var = ttk.Label(info, text="")
        self.cat_var.grid(row=3, column=0, sticky="w", pady=2)

        ttk.Separator(self.content).pack(fill="x", pady=12)

        actions = ttk.Frame(self.content)
        actions.pack(anchor="nw")

        ttk.Label(actions, text="Quantity:").pack(side="left")
        self.qty = ttk.Spinbox(actions, from_=1, to=999, width=6)
        self.qty.set("1")
        self.qty.pack(side="left", padx=6)

        ttk.Button(actions, text="Add to Cart", command=self.add_to_cart).pack(side="left", padx=8)

        self.pic_hint = ttk.Label(
            self.content,
            text="Pictures: (Stage 2.4/2.5 – will render thumbnails)",
            style="Muted.TLabel",
        )
        self.pic_hint.pack(anchor="nw", pady=(12, 0))

    def on_show(self):
        self.load_item()

    def load_item(self):
        item_id = self.state.selected_item_id
        if not item_id:
            self.set_status("No item selected")
            return

        result = store_app_service.ui_item_details(item_id)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.item = result.data
        self.header.config(text=f'{self.item["name"]}  (ID: {self.item["id"]})')
        self.desc.config(text=self.item.get("description") or "")

        d = self.item["dimensions"]
        self.dim_var.config(text=f'Dimensions (L×W×H): {d["length"]} × {d["width"]} × {d["height"]} cm')
        self.weight_var.config(text=f'Weight: {self.item["weight"]} kg')
        self.price_var.config(text=f'Price: {self.item["price"]:.2f} {self.item["currency"]}')

        cats = self.item.get("categories") or []
        self.cat_var.config(text=f"Categories: {', '.join(cats) if cats else '-'}")

        self.set_status("Item loaded")

    def add_to_cart(self):
        if not self.state.is_logged_in:
            self.set_status("Please login first")
            messagebox.showinfo("Login required", "Please login to add items to cart.")
            return

        if not self.item:
            self.set_status("No item loaded")
            return

        try:
            q = int(self.qty.get())
        except Exception:
            self.set_status("Invalid quantity")
            return

        if q <= 0:
            self.set_status("Quantity must be positive")
            return

        user_id = self.state.session.user_id
        result = store_app_service.ui_add_to_cart(user_id, item_id=int(self.item["id"]), quantity=q)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.set_status("Added to cart")
        messagebox.showinfo("Added", "Item added to cart successfully.")

    def _view_3d_stub(self):
        # Stage 3: VPython integration
        messagebox.showinfo("3D", "3D viewer will be added in Stage 3 (VPython).")
