from __future__ import annotations

from tkinter import ttk
from app.ui.views.base_view import BaseView


class LoginView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state, on_state_changed):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Login",
            subtitle="Stage 2.1: session + navigation (still no backend calls).",
        )
        self.state = state
        self.on_state_changed = on_state_changed

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

        ttk.Separator(self.content).pack(fill="x", pady=10)

        ttk.Label(self.content, text="Quick demo login (no backend):", style="Muted.TLabel").pack(anchor="nw", pady=(0, 6))
        quick = ttk.Frame(self.content)
        quick.pack(anchor="nw")

        ttk.Button(quick, text="Login as Customer", command=self._login_customer_demo).pack(side="left")
        ttk.Button(quick, text="Login as Admin", command=self._login_admin_demo).pack(side="left", padx=8)

    def _login_stub(self):
        email = self.email.get().strip()
        if email:
            self.set_status(f"Entered email: {email} (not logged in)")
        else:
            self.set_status("Please enter email (stub)")

    def _login_customer_demo(self):
        self.state.set_session(user_id=1, username="demo_customer", email="customer@demo", role="CUSTOMER", currency="EUR")
        self.on_state_changed()
        self.set_status("Logged in (demo customer)")
        self.on_navigate("catalog")

    def _login_admin_demo(self):
        self.state.set_session(user_id=2, username="demo_admin", email="admin@demo", role="ADMIN", currency="EUR")
        self.on_state_changed()
        self.set_status("Logged in (demo admin)")
        self.on_navigate("catalog")
