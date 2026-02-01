from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, messagebox

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class ManageItemsView(BaseView):
    """
    ADMIN view: CRUD Items (safe).
    Uses StoreAppService admin methods (direct SQL).
    """

    def __init__(self, parent, *, on_navigate, set_status, state):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Manage Items",
            subtitle="Admin: create / edit / delete items (base currency EUR).",
        )
        self.state = state

        top = ttk.Frame(self.content)
        top.pack(anchor="nw", fill="x")

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(top, text="New Item", command=self.new_item).pack(side="left", padx=8)
        ttk.Button(top, text="Edit Selected", command=self.edit_selected).pack(side="left", padx=8)
        ttk.Button(top, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=8)
        ttk.Button(top, text="Back to Catalog", command=lambda: self.on_navigate("catalog")).pack(side="left", padx=8)

        self.tree = ttk.Treeview(
            self.content,
            columns=("id", "name", "price", "weight"),
            show="headings",
            height=14,
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("price", text="Price (EUR)")
        self.tree.heading("weight", text="Weight (kg)")

        self.tree.column("id", width=70, stretch=False, anchor="center")
        self.tree.column("name", width=520, stretch=True)
        self.tree.column("price", width=140, stretch=False, anchor="e")
        self.tree.column("weight", width=120, stretch=False, anchor="e")

        self.tree.pack(fill="both", expand=True, pady=10)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

    def on_show(self):
        self.refresh()

    def _selected_item_id(self) -> int | None:
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

        if not self.state.is_logged_in or self.state.role != "ADMIN":
            self.set_status("Manage Items is available for ADMIN only")
            return

        res = store_app_service.ui_admin_list_items()
        if not res.ok:
            self.set_status(res.error.message)
            return

        items = res.data or []
        if not items:
            self.set_status("No items found")
            return

        for it in items:
            item_id = int(it["id"])
            self.tree.insert(
                "",
                "end",
                iid=str(item_id),
                values=(
                    item_id,
                    it.get("name", ""),
                    f'{float(it.get("price", 0.0)):.2f}',
                    f'{float(it.get("weight", 0.0)):.2f}',
                ),
            )

        self.set_status(f"Loaded {len(items)} items (admin)")

    # ---------------- Dialogs ----------------

    def new_item(self):
        if not self.state.is_logged_in or self.state.role != "ADMIN":
            self.set_status("Admin only")
            return
        self._open_editor(title="New Item", item=None)

    def edit_selected(self):
        if not self.state.is_logged_in or self.state.role != "ADMIN":
            self.set_status("Admin only")
            return

        item_id = self._selected_item_id()
        if not item_id:
            self.set_status("Select an item first")
            return

        res = store_app_service.ui_admin_get_item(item_id)
        if not res.ok:
            self.set_status(res.error.message)
            return

        self._open_editor(title=f"Edit Item (ID: {item_id})", item=res.data)

    def delete_selected(self):
        if not self.state.is_logged_in or self.state.role != "ADMIN":
            self.set_status("Admin only")
            return

        item_id = self._selected_item_id()
        if not item_id:
            self.set_status("Select an item first")
            return

        if not messagebox.askyesno("Delete", f"Delete item ID {item_id}?"):
            return

        res = store_app_service.ui_admin_delete_item(item_id)
        if not res.ok:
            self.set_status(res.error.message)
            return

        self.set_status("Item deleted")
        self.refresh()

    # ---------------- Helpers ----------------

    def _project_root(self) -> str:
        # OmniStore/
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    def _normalize_picture_name(self, p: str) -> str:
        """
        Accept:
          - table_1.png
          - images/table_1.png
          - images\\table_1.png
        Return:
          - table_1.png
        """
        p = (p or "").strip()
        if not p:
            return ""
        p = p.replace("\\", "/")
        if p.lower().startswith("images/"):
            p = p.split("/", 1)[1]
        return p.strip()

    def _parse_pictures(self, s: str) -> list[str]:
        raw = (s or "").replace(";", ",").replace("\n", ",")
        parts = [x.strip() for x in raw.split(",") if x.strip()]
        out: list[str] = []
        seen = set()
        for x in parts:
            x = self._normalize_picture_name(x)
            if x and x not in seen:
                out.append(x)
                seen.add(x)
        return out

    def _validate_pictures_exist(self, names: list[str]) -> tuple[bool, str]:
        if not names:
            return True, ""
        root = self._project_root()
        img_dir = os.path.join(root, "images")
        missing = []
        for n in names:
            p = os.path.join(img_dir, n)
            if not os.path.exists(p):
                missing.append(n)
        if missing:
            return False, "Missing image files in /images: " + ", ".join(missing)
        return True, ""

    def _open_editor(self, *, title: str, item: dict | None):
        win = tk.Toplevel(self.content)
        win.title(title)
        win.transient(self.content.winfo_toplevel())
        win.grab_set()

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        # Fields
        ttk.Label(frm, text="Name:").grid(row=0, column=0, sticky="w", pady=4)
        ent_name = ttk.Entry(frm, width=52)
        ent_name.grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="Description:").grid(row=1, column=0, sticky="nw", pady=4)
        txt_desc = tk.Text(frm, width=52, height=6)
        txt_desc.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="Price (EUR):").grid(row=2, column=0, sticky="w", pady=4)
        ent_price = ttk.Entry(frm, width=18)
        ent_price.grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="Weight (kg):").grid(row=3, column=0, sticky="w", pady=4)
        ent_weight = ttk.Entry(frm, width=18)
        ent_weight.grid(row=3, column=1, sticky="w", pady=4)

        # Dimensions: your DB uses Height/Width/Depth, but UI keeps (Length/Width/Height)
        ttk.Label(frm, text="Length (cm):").grid(row=4, column=0, sticky="w", pady=4)
        ent_len = ttk.Entry(frm, width=18)
        ent_len.grid(row=4, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="Width (cm):").grid(row=5, column=0, sticky="w", pady=4)
        ent_wid = ttk.Entry(frm, width=18)
        ent_wid.grid(row=5, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="Height (cm):").grid(row=6, column=0, sticky="w", pady=4)
        ent_hei = ttk.Entry(frm, width=18)
        ent_hei.grid(row=6, column=1, sticky="w", pady=4)

        # Pictures
        ttk.Label(frm, text="Pictures (filenames):").grid(row=7, column=0, sticky="nw", pady=4)
        txt_pics = tk.Text(frm, width=52, height=3)
        txt_pics.grid(row=7, column=1, sticky="w", pady=4)
        hint = ttk.Label(frm, text="Example: chair_1.png, desk_2.png (must exist in /images)", style="Muted.TLabel")
        hint.grid(row=8, column=1, sticky="w", pady=(0, 6))

        # Categories (multi-select)
        ttk.Label(frm, text="Categories:").grid(row=9, column=0, sticky="nw", pady=4)
        lst_cats = tk.Listbox(frm, width=52, height=6, selectmode="multiple", exportselection=False)
        lst_cats.grid(row=9, column=1, sticky="w", pady=4)

        # Load all categories
        res_cats = store_app_service.ui_admin_list_categories()
        all_cats = res_cats.data if res_cats.ok else []
        # map index -> category_id
        cat_ids_by_idx = []
        for c in all_cats:
            lst_cats.insert("end", c["name"])
            cat_ids_by_idx.append(int(c["id"]))

        # Prefill
        if item:
            ent_name.insert(0, item.get("name", "") or "")
            txt_desc.insert("1.0", item.get("description", "") or "")
            ent_price.insert(0, f'{float(item.get("price", 0.0)):.2f}')
            ent_weight.insert(0, f'{float(item.get("weight", 0.0)):.2f}')

            ent_len.insert(0, f'{float(item.get("length", 0.0)):.2f}')
            ent_wid.insert(0, f'{float(item.get("width", 0.0)):.2f}')
            ent_hei.insert(0, f'{float(item.get("height", 0.0)):.2f}')

            pics = item.get("pictures") or []
            fnames = []
            for p in pics:
                p = str(p).replace("\\", "/")
                if p.lower().startswith("images/"):
                    fnames.append(p.split("/", 1)[1])
                else:
                    fnames.append(p)
            txt_pics.insert("1.0", ", ".join(fnames))

            selected = set(item.get("category_ids") or [])
            for idx, cid in enumerate(cat_ids_by_idx):
                if cid in selected:
                    lst_cats.selection_set(idx)
        else:
            ent_price.insert(0, "0.00")
            ent_weight.insert(0, "0.00")
            ent_len.insert(0, "0.00")
            ent_wid.insert(0, "0.00")
            ent_hei.insert(0, "0.00")

        btns = ttk.Frame(frm)
        btns.grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 0))

        def on_save():
            name = ent_name.get().strip()
            desc = txt_desc.get("1.0", "end").strip()

            if not name:
                messagebox.showerror("Validation", "Name is required")
                return

            try:
                price = float(ent_price.get().strip())
            except Exception:
                messagebox.showerror("Validation", "Invalid price")
                return
            if price < 0:
                messagebox.showerror("Validation", "Price cannot be negative")
                return

            try:
                weight = float(ent_weight.get().strip())
            except Exception:
                messagebox.showerror("Validation", "Invalid weight")
                return
            if weight < 0:
                messagebox.showerror("Validation", "Weight cannot be negative")
                return

            try:
                length = float(ent_len.get().strip())
                width = float(ent_wid.get().strip())
                height = float(ent_hei.get().strip())
            except Exception:
                messagebox.showerror("Validation", "Invalid dimensions (length/width/height)")
                return
            if length < 0 or width < 0 or height < 0:
                messagebox.showerror("Validation", "Dimensions cannot be negative")
                return

            pic_names = self._parse_pictures(txt_pics.get("1.0", "end").strip())
            ok, msg = self._validate_pictures_exist(pic_names)
            if not ok:
                messagebox.showerror("Validation", msg)
                return

            if not self.state.is_logged_in or self.state.role != "ADMIN":
                messagebox.showerror("Error", "Admin session missing")
                return

            admin_user_id = int(self.state.session.user_id)

            sel_idx = list(lst_cats.curselection() or [])
            selected_cat_ids = [cat_ids_by_idx[i] for i in sel_idx if 0 <= i < len(cat_ids_by_idx)]

            if item is None:
                res = store_app_service.ui_admin_create_item(
                    admin_user_id=admin_user_id,
                    name=name,
                    description=desc,
                    price=price,
                    weight=weight,
                    length=length,
                    width=width,
                    height=height,
                    pictures=pic_names,
                    category_ids=selected_cat_ids,
                )
            else:
                res = store_app_service.ui_admin_update_item(
                    item_id=int(item["id"]),
                    name=name,
                    description=desc,
                    price=price,
                    weight=weight,
                    length=length,
                    width=width,
                    height=height,
                    pictures=pic_names,
                    category_ids=selected_cat_ids,
                )

            if not res.ok:
                messagebox.showerror("Error", res.error.message)
                return

            win.destroy()
            self.set_status("Saved")
            self.refresh()

        ttk.Button(btns, text="Save", command=on_save).pack(side="left")
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=8)
