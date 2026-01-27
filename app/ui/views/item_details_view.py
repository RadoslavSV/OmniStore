from __future__ import annotations

from tkinter import ttk, messagebox

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service

import os
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

class ItemDetailsView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Item Details",
        )
        self.state = state
        self.item = None  # DTO dict

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Back to Catalog", command=lambda: self.on_navigate("catalog")).pack(side="left")
        ttk.Button(top, text="Go to Cart", command=lambda: self.on_navigate("cart")).pack(side="left", padx=8)
        ttk.Button(top, text="View 3D (stub)", command=self._view_3d_stub).pack(side="left", padx=8)

        self.image_label = ttk.Label(self.content)
        self.image_label.pack(anchor="nw", pady=(8, 12))

        self._tk_image = None  # IMPORTANT: keep reference

        self.header = ttk.Label(self.content, text="", style="Title.TLabel")
        self.header.pack(anchor="nw", pady=(12, 4))

        self.desc = ttk.Label(self.content, text="", wraplength=780, justify="left")
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
        actions.pack(anchor="nw", fill="x")

        ttk.Label(actions, text="Quantity:").pack(side="left")
        self.qty = ttk.Spinbox(actions, from_=1, to=999, width=6)
        self.qty.set("1")
        self.qty.pack(side="left", padx=6)

        ttk.Button(actions, text="Add to Cart", command=self.add_to_cart).pack(side="left", padx=8)
        ttk.Button(actions, text="Add to Favorites", command=self.add_to_favorites).pack(side="left", padx=8)
        ttk.Button(actions, text="Remove Favorite", command=self.remove_favorite).pack(side="left", padx=8)

        ttk.Separator(self.content).pack(fill="x", pady=12)

        pics = ttk.Frame(self.content)
        pics.pack(anchor="nw", fill="both", expand=True)

        ttk.Label(pics, text="Main picture path:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.main_pic_var = ttk.Label(pics, text="-")
        self.main_pic_var.grid(row=1, column=0, sticky="w", pady=(0, 8))

        ttk.Label(pics, text="All pictures (paths):", style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        self.pics_list = ttk.Treeview(pics, columns=("path",), show="headings", height=6)
        self.pics_list.heading("path", text="FilePath")
        self.pics_list.column("path", width=740, stretch=True)
        self.pics_list.grid(row=3, column=0, sticky="nsew", pady=(6, 0))

        pics.grid_rowconfigure(3, weight=1)
        pics.grid_columnconfigure(0, weight=1)

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

        # Record view (History) - only for logged-in customers
        if self.state.is_logged_in and self.state.role == "CUSTOMER":
            store_app_service.ui_record_view(self.state.session.user_id, int(self.item["id"]))

        # Header + description
        self.header.config(text=f'{self.item["name"]}  (ID: {self.item["id"]})')
        self.desc.config(text=self.item.get("description") or "")

        # Specs
        d = self.item["dimensions"]
        self.dim_var.config(text=f'Dimensions (L×W×H): {d["length"]} × {d["width"]} × {d["height"]} cm')
        self.weight_var.config(text=f'Weight: {self.item["weight"]} kg')
        self.price_var.config(text=f'Price: {self.item["price"]:.2f} {self.item["currency"]}')

        cats = self.item.get("categories") or []
        self.cat_var.config(text=f"Categories: {', '.join(cats) if cats else '-'}")

        # Pictures (paths only)
        self.main_pic_var.config(text=self.item.get("main_picture") or "-")
        self._load_image(self.item.get("main_picture"))

        for i in self.pics_list.get_children():
            self.pics_list.delete(i)

        for p in (self.item.get("pictures") or []):
            self.pics_list.insert("", "end", values=(p,))

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
        messagebox.showinfo("3D", "3D viewer will be added in Stage 4 (VPython).")

    def add_to_favorites(self):
        if not self.state.is_logged_in or self.state.role != "CUSTOMER":
            self.set_status("Favorites are available for customers (please login)")
            return
        if not self.item:
            self.set_status("No item loaded")
            return

        user_id = self.state.session.user_id
        item_id = int(self.item["id"])
        result = store_app_service.ui_add_favorite(user_id, item_id)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.set_status("Added to favorites")
        messagebox.showinfo("Favorites", "Added to favorites.")

    def remove_favorite(self):
        if not self.state.is_logged_in or self.state.role != "CUSTOMER":
            self.set_status("Favorites are available for customers (please login)")
            return
        if not self.item:
            self.set_status("No item loaded")
            return

        user_id = self.state.session.user_id
        item_id = int(self.item["id"])
        result = store_app_service.ui_remove_favorite(user_id, item_id)
        if not result.ok:
            self.set_status(result.error.message)
            return

        self.set_status("Removed from favorites")
        messagebox.showinfo("Favorites", "Removed from favorites.")

    def _load_image(self, path: str, max_size=(360, 360)):
        if not path:
            self.image_label.config(text="No image")
            return

        if not os.path.exists(path):
            self.image_label.config(text=f"Image not found: {path}")
            return

        try:
            img = Image.open(path)
            img.thumbnail(max_size)
            self._tk_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self._tk_image, text="")
        except Exception as e:
            self.image_label.config(text=f"Failed to load image: {e}")
