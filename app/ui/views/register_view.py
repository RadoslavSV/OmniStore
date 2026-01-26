from __future__ import annotations

from tkinter import ttk
from app.ui.views.base_view import BaseView


class RegisterView(BaseView):
    def __init__(self, parent, *, on_navigate, set_status):
        super().__init__(
            parent,
            on_navigate=on_navigate,
            set_status=set_status,
            title="Register",
            subtitle="Stage 1: UI only. Stage 2 will call backend facade.",
        )

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

        ttk.Button(btns, text="Register (stub)", command=self._register_stub).pack(side="left")
        ttk.Button(btns, text="Go to Login", command=lambda: self.on_navigate("login")).pack(side="left", padx=8)

    def _register_stub(self):
        email = self.entries["email"].get().strip()
        self.set_status(f"Register stub: {email or '(no email)'}")
