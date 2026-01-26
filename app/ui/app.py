import tkinter as tk

from app.db.schema import init_db
from app.db.seed import seed_demo_data_if_empty
from app.ui.main_window import MainWindow


def run_app():
    init_db()
    seed_demo_data_if_empty()

    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
