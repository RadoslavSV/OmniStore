from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Item3DInfo:
    title: str
    length: float
    width: float
    height: float
    weight: Optional[float] = None
    price: Optional[float] = None
    currency: str = "EUR"


def launch_vpython_viewer(info: Item3DInfo) -> None:
    """
    Launch VPython viewer in a separate process (prevents Tkinter freeze).
    """
    cmd = [
        sys.executable,
        "-m",
        "app.ui.vpython_viewer",
        "--title", str(info.title),
        "--length", str(info.length),
        "--width", str(info.width),
        "--height", str(info.height),
        "--currency", str(info.currency),
    ]

    if info.weight is not None:
        cmd += ["--weight", str(info.weight)]
    if info.price is not None:
        cmd += ["--price", str(info.price)]

    kwargs = {"close_fds": True}

    # Windows: open in a separate console, non-blocking
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

    subprocess.Popen(cmd, **kwargs)
