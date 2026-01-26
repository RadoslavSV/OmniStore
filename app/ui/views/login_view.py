from __future__ import annotations

from tkinter import ttk

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class LoginView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state, on_state_changed):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Login",
            subtitle="Stage 2.2: real login via StoreAppService.",
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

        ttk.Button(btns, text="Login", command=self._login).pack(side="left")
        ttk.Button(btns, text="Go to Register", command=lambda: self.on_navigate("register")).pack(side="left", padx=8)

    def _login(self):
        email = self.email.get().strip()
        password = self.password.get().strip()

        if not email or not password:
            self.set_status("Please enter email and password")
            return

        result = store_app_service.ui_login(email, password)
        if not result.ok:
            self.set_status(result.error.message)
            return

        user = result.data
        # Currency in stage 2.2: keep EUR (no API usage)
        self.state.set_session(user_id=user.id, username=user.username, email=user.email, role=user.role, currency="EUR")
        self.on_state_changed()
        self.set_status("Logged in successfully")
        self.on_navigate("catalog")
