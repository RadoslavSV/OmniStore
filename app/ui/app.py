import tkinter as tk
from app.ui.main_window import MainWindow


def run_app():
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
