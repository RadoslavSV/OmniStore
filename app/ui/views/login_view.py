from __future__ import annotations

from tkinter import ttk
from app.ui.views.base_view import BaseView


class LoginView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Login",
            subtitle="Stage 1: UI only (no backend calls yet).",
        )

        form = ttk.Frame(self.content)
        form.pack(anchor="nw")

        ttk.Label(form, text="Email:").grid(row=0, column=0, sticky="w", pady=4)
        self.email = ttk.Entry(form, width=36)
        self.email.grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w", pady=4)
        self.password = ttk.Entry(form, width=36, show="*")
        self.password.grid(row=1, column=1, sticky="w", pady=4)

        btns = ttk.Frame(self.content)
        btns.pack(anchor="nw", pady=10)

        ttk.Button(btns, text="Login (stub)", command=self._login_stub).pack(side="left")
        ttk.Button(btns, text="Go to Register", command=lambda: self.on_navigate("register")).pack(side="left", padx=8)

    def _login_stub(self):
        # Stage 2 will call StoreAppService.ui_login(...)
        email = self.email.get().strip()
        if email:
            self.set_status(f"Entered email: {email} (not logged in)")
        else:
            self.set_status("Please enter email (stub)")
