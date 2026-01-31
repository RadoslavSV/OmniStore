from __future__ import annotations

import os
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service

from app.ui.three_d_launcher import launch_vpython_viewer, Item3DInfo


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

        # picture carousel state
        self._pictures: list[str] = []
        self._pic_index: int = 0
        self._tk_image = None  # keep reference

        # ----- Top nav -----
        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Back to Catalog", command=lambda: self.on_navigate("catalog")).pack(side="left")
        ttk.Button(top, text="Go to Cart", command=lambda: self.on_navigate("cart")).pack(side="left", padx=8)
        ttk.Button(top, text="View 3D (stub)", command=self._view_3d_stub).pack(side="left", padx=8)

        ttk.Separator(self.content).pack(fill="x", pady=(10, 12))

        # ----- Main layout: left info + right image -----
        body = ttk.Frame(self.content)
        body.pack(fill="both", expand=True)

        self.left = ttk.Frame(body)
        self.left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.right = ttk.Frame(body)
        self.right.pack(side="right", fill="y")

        # ----- Left: text info -----
        self.header = ttk.Label(self.left, text="", style="ContentTitle.TLabel")
        self.header.pack(anchor="nw", pady=(0, 4))

        self.desc = ttk.Label(self.left, text="", wraplength=720, justify="left")
        self.desc.pack(anchor="nw", pady=(0, 10))

        info = ttk.Frame(self.left)
        info.pack(anchor="nw", fill="x")

        self.dim_var = ttk.Label(info, text="")
        self.dim_var.grid(row=0, column=0, sticky="w", pady=2)

        self.weight_var = ttk.Label(info, text="")
        self.weight_var.grid(row=1, column=0, sticky="w", pady=2)

        self.price_var = ttk.Label(info, text="")
        self.price_var.grid(row=2, column=0, sticky="w", pady=2)

        self.cat_var = ttk.Label(info, text="")
        self.cat_var.grid(row=3, column=0, sticky="w", pady=2)

        ttk.Separator(self.left).pack(fill="x", pady=12)

        actions = ttk.Frame(self.left)
        actions.pack(anchor="nw", fill="x")

        ttk.Label(actions, text="Quantity:").pack(side="left")
        self.qty = ttk.Spinbox(actions, from_=1, to=999, width=6)
        self.qty.set("1")
        self.qty.pack(side="left", padx=6)

        ttk.Button(actions, text="Add to Cart", command=self.add_to_cart).pack(side="left", padx=8)
        ttk.Button(actions, text="Add to Favorites", command=self.add_to_favorites).pack(side="left", padx=8)
        ttk.Button(actions, text="Remove Favorite", command=self.remove_favorite).pack(side="left", padx=8)

        # ----- Right: image + arrows -----
        carousel = ttk.Frame(self.right)
        carousel.pack(anchor="ne")

        self.btn_prev = ttk.Button(carousel, text="◀", width=3, command=self._prev_picture)
        self.btn_prev.grid(row=0, column=0, padx=(0, 6), sticky="n")

        self.image_label = ttk.Label(carousel, text="No image")
        self.image_label.grid(row=0, column=1, sticky="n")

        self.btn_next = ttk.Button(carousel, text="▶", width=3, command=self._next_picture)
        self.btn_next.grid(row=0, column=2, padx=(6, 0), sticky="n")

        self.pic_counter = ttk.Label(self.right, text="", style="Muted.TLabel")
        self.pic_counter.pack(anchor="ne", pady=(6, 0))

        self._update_carousel_controls()

    def on_show(self):
        self.load_item()

    def _display_currency(self) -> str:
        if not self.state.is_logged_in or not getattr(self.state, "session", None):
            return "EUR"
        c = getattr(self.state.session, "currency", None) or "EUR"
        return str(c).upper()

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

        # ---- Convert price for display currency (Catalog/Details were stuck on EUR) ----
        try:
            target = self._display_currency()
            base_cur = str(self.item.get("currency") or "EUR").upper()
            base_price = float(self.item.get("price") or 0.0)

            if target and target != base_cur:
                # Use the same CurrencyService instance through StoreAppService
                converted = store_app_service.currency.convert(base_price, to_currency=target, from_currency=base_cur)
                self.item["price"] = float(converted)
                self.item["currency"] = target
        except Exception:
            # If conversion fails, keep original price/currency (safe)
            pass

        # Header + description
        self.header.config(text=f'{self.item["name"]}  (ID: {self.item["id"]})')
        self.desc.config(text=self.item.get("description") or "")

        # Specs
        d = self.item["dimensions"]
        self.dim_var.config(text=f'Dimensions (L×W×H): {d["length"]} × {d["width"]} × {d["height"]} cm')
        self.weight_var.config(text=f'Weight: {self.item["weight"]} kg')
        self.price_var.config(text=f'Price: {float(self.item["price"]):.2f} {self.item["currency"]}')

        cats = self.item.get("categories") or []
        self.cat_var.config(text=f"Categories: {', '.join(cats) if cats else '-'}")

        # Pictures carousel
        self._pictures = list(self.item.get("pictures") or [])
        main = self.item.get("main_picture")

        self._pic_index = 0
        if main and self._pictures:
            try:
                self._pic_index = self._pictures.index(main)
            except ValueError:
                self._pic_index = 0

        self._show_current_picture()
        self.set_status("Item loaded")

    # ---------------- Pictures carousel ----------------

    def _update_carousel_controls(self):
        n = len(self._pictures)
        if n <= 1:
            self.btn_prev.state(["disabled"])
            self.btn_next.state(["disabled"])
            self.pic_counter.config(text="" if n == 0 else "1/1")
        else:
            self.btn_prev.state(["!disabled"])
            self.btn_next.state(["!disabled"])
            self.pic_counter.config(text=f"{self._pic_index + 1}/{n}")

    def _prev_picture(self):
        if not self._pictures:
            return
        self._pic_index = (self._pic_index - 1) % len(self._pictures)
        self._show_current_picture()

    def _next_picture(self):
        if not self._pictures:
            return
        self._pic_index = (self._pic_index + 1) % len(self._pictures)
        self._show_current_picture()

    def _show_current_picture(self):
        if not self._pictures:
            self._tk_image = None
            self.image_label.config(image="", text="No image")
            self._update_carousel_controls()
            return

        path = self._pictures[self._pic_index]
        self._load_image(path)
        self._update_carousel_controls()

    def _load_image(self, path: str, frame_size=(420, 320), bg_color=(0, 0, 0)):
        self._tk_image = None
        self.image_label.config(image="", text="")

        if not path:
            frame = Image.new("RGB", frame_size, bg_color)
            self._tk_image = ImageTk.PhotoImage(frame)
            self.image_label.config(image=self._tk_image, text="")
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        abs_path = os.path.normpath(os.path.join(project_root, path))

        if not os.path.exists(abs_path):
            frame = Image.new("RGB", frame_size, bg_color)
            self._tk_image = ImageTk.PhotoImage(frame)
            self.image_label.config(image=self._tk_image, text="")
            return

        try:
            img = Image.open(abs_path)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            fw, fh = frame_size
            iw, ih = img.size

            scale = min(fw / iw, fh / ih)
            new_w = max(1, int(iw * scale))
            new_h = max(1, int(ih * scale))

            resized = img.resize((new_w, new_h), Image.LANCZOS)

            frame = Image.new("RGB", (fw, fh), bg_color)

            if resized.mode == "RGBA":
                tmp = Image.new("RGBA", (fw, fh), bg_color + (255,))
                x = (fw - new_w) // 2
                y = (fh - new_h) // 2
                tmp.paste(resized, (x, y), resized)
                frame = tmp.convert("RGB")
            else:
                x = (fw - new_w) // 2
                y = (fh - new_h) // 2
                frame.paste(resized, (x, y))

            self._tk_image = ImageTk.PhotoImage(frame)
            self.image_label.config(image=self._tk_image, text="")
        except Exception:
            frame = Image.new("RGB", frame_size, bg_color)
            self._tk_image = ImageTk.PhotoImage(frame)
            self.image_label.config(image=self._tk_image, text="")

    # ---------------- Actions ----------------

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

    def _view_3d_stub(self):
        if not self.item:
            messagebox.showinfo("3D", "No item loaded.")
            return

        d = self.item.get("dimensions") or {}
        try:
            info = Item3DInfo(
                title=self.item.get("name") or "Item",
                length=float(d["length"]),
                width=float(d["width"]),
                height=float(d["height"]),
                weight=float(self.item.get("weight")) if self.item.get("weight") is not None else None,
                price=float(self.item.get("price")) if self.item.get("price") is not None else None,
                currency=str(self.item.get("currency") or "EUR"),
            )
        except Exception:
            messagebox.showerror("3D", "Item dimensions are missing/invalid.")
            return

        launch_vpython_viewer(info)
        self.set_status("Opened 3D viewer")
