from __future__ import annotations

from tkinter import ttk

from app.ui.views.base_view import BaseView
from app.ui.service_provider import store_app_service


class RegisterView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state, on_state_changed):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Register",
            subtitle="Stage 2.2: real registration via StoreAppService.",
        )
        self.state = state
        self.on_state_changed = on_state_changed

        form = ttk.Frame(self.content)
        form.pack(anchor="nw")

        fields = [
            ("Username:", "username"),
            ("Name:", "name"),
            ("Email:", "email"),
            ("Password:", "password"),
        ]
        self.entries = {}

        for r, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=r, column=0, sticky="w", pady=4)
            ent = ttk.Entry(form, width=36, show="*" if key == "password" else "")
            ent.grid(row=r, column=1, sticky="w", pady=4)
            self.entries[key] = ent

        btns = ttk.Frame(self.content)
        btns.pack(anchor="nw", pady=10)

        ttk.Button(btns, text="Register", command=self._register).pack(side="left")
        ttk.Button(btns, text="Go to Login", command=lambda: self.on_navigate("login")).pack(side="left", padx=8)

    def _register(self):
        username = self.entries["username"].get().strip()
        name = self.entries["name"].get().strip()
        email = self.entries["email"].get().strip()
        password = self.entries["password"].get().strip()

        if not username or not name or not email or not password:
            self.set_status("Please fill all fields")
            return

        result = store_app_service.ui_register_customer(
            username=username,
            email=email,
            name=name,
            password=password,
            currency="EUR",
        )
        if not result.ok:
            self.set_status(result.error.message)
            return

        user = result.data
        self.state.set_session(user_id=user.id, username=user.username, email=user.email, role=user.role, currency="EUR")
        self.on_state_changed()
        self.set_status("Registered and logged in")
        self.on_navigate("catalog")
