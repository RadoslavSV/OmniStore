from __future__ import annotations

from tkinter import ttk, messagebox
from typing import Optional, Callable, List

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class CurrencyView(BaseView):
    """
    UI for selecting application currency.
    Purpose:
    - NOT a converter
    - Select one currency
    - Save it per customer
    - Refresh UI prices automatically (via callback)
    """

    def __init__(
        self,
        parent,
        *,
        on_navigate,
        set_status,
        state,
        on_currency_changed: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Currency",
        )
        self.state = state
        self.on_currency_changed = on_currency_changed

        info = ttk.Label(
            self.content,
            text="Select the currency in which prices will be displayed across the application.",
            wraplength=650,
        )
        info.pack(anchor="nw", pady=(0, 12))

        form = ttk.Frame(self.content)
        form.pack(anchor="nw")

        ttk.Label(form, text="Currency:").grid(row=0, column=0, sticky="w", pady=4)

        self.currency_box = ttk.Combobox(form, state="readonly", width=12)
        self.currency_box.grid(row=0, column=1, sticky="w", padx=8)

        btns = ttk.Frame(self.content)
        btns.pack(anchor="nw", pady=12)

        ttk.Button(btns, text="Save", command=self.save_currency).pack(side="left")
        ttk.Button(btns, text="Back to Catalog", command=lambda: self.on_navigate("catalog")).pack(side="left", padx=8)

    def on_show(self):
        # Currency selection only for logged-in customers
        if not self.state.is_logged_in or self.state.role != "CUSTOMER":
            self.set_status("Currency selection is available for logged-in customers")
            return

        # Load supported currencies via StoreAppService (UI-safe)
        res = store_app_service.ui_list_supported_currencies()
        if not res.ok:
            self.set_status(res.error.message)
            currencies: List[str] = ["EUR"]
        else:
            currencies = res.data or ["EUR"]

        # Ensure EUR is present
        currencies = [str(c).upper() for c in currencies if c]
        if "EUR" not in currencies:
            currencies = ["EUR"] + [c for c in currencies if c != "EUR"]

        self.currency_box["values"] = currencies

        # Prefer session currency; fallback to persisted currency if needed
        current = (getattr(self.state.session, "currency", None) or "EUR").upper()
        if current not in currencies:
            cur_res = store_app_service.ui_get_customer_currency(self.state.session.user_id)
            if cur_res.ok and cur_res.data:
                current = str(cur_res.data).upper()

        if current in currencies:
            self.currency_box.set(current)
        else:
            self.currency_box.set("EUR")

        self.set_status("Select display currency")

    def save_currency(self):
        if not self.state.is_logged_in or self.state.role != "CUSTOMER":
            self.set_status("Please login as customer first")
            return

        currency = (self.currency_box.get() or "").strip().upper()
        if not currency:
            self.set_status("Please select a currency")
            return

        user_id = self.state.session.user_id

        # Persist currency in DB via StoreAppService (UI-safe)
        res = store_app_service.ui_set_customer_currency(user_id, currency)
        if not res.ok:
            self.set_status(res.error.message)
            return

        # Update UI session state
        self.state.session.currency = currency

        self.set_status(f"Currency set to {currency}")
        messagebox.showinfo("Currency", f"Currency changed to {currency}")

        # Notify main window so it can refresh price-based views
        if self.on_currency_changed is not None:
            try:
                self.on_currency_changed()
            except Exception:
                pass

        self.on_navigate("catalog")
