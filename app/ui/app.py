import tkinter as tk

from app.db.schema import init_db
from app.ui.main_window import MainWindow


def run_app():
    init_db()  # ensure tables exist (safe to call multiple times)
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
