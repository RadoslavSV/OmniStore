from __future__ import annotations

from tkinter import ttk
from app.ui.views.base_view import BaseView


class RegisterView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status, state, on_state_changed):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Register",
            subtitle="Stage 2.1: fills session (demo). Stage 2.2 will call backend facade.",
        )
        self.state = state
        self.on_state_changed = on_state_changed

        form = ttk.Frame(self.content)
        form.pack(anchor="nw")

        fields = [("Username:", "username"), ("Name:", "name"), ("Email:", "email"), ("Password:", "password")]
        self.entries = {}

        for r, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=r, column=0, sticky="w", pady=4)
            ent = ttk.Entry(form, width=36, show="*" if key == "password" else "")
            ent.grid(row=r, column=1, sticky="w", pady=4)
            self.entries[key] = ent

        btns = ttk.Frame(self.content)
        btns.pack(anchor="nw", pady=10)

        ttk.Button(btns, text="Register (demo)", command=self._register_demo).pack(side="left")
        ttk.Button(btns, text="Go to Login", command=lambda: self.on_navigate("login")).pack(side="left", padx=8)

    def _register_demo(self):
        username = self.entries["username"].get().strip() or "new_user"
        email = self.entries["email"].get().strip() or "new@user"
        self.state.set_session(user_id=99, username=username, email=email, role="CUSTOMER", currency="EUR")
        self.on_state_changed()
        self.set_status("Registered (demo) and logged in")
        self.on_navigate("catalog")
