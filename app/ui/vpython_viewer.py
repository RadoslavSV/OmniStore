from __future__ import annotations

import argparse
from vpython import (
    canvas, box, vector, color, arrow, label, rate,
    cylinder, sphere
)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _nice_scale(length_cm: float, width_cm: float, height_cm: float) -> tuple[float, float, float, float]:
    """
    Scale cm dimensions to VPython scene units so it looks good.
    Returns: (L, W, H, scale) where L/W/H are scene units and scale is units-per-cm.
    """
    length_cm = max(0.1, float(length_cm))
    width_cm = max(0.1, float(width_cm))
    height_cm = max(0.1, float(height_cm))

    max_dim = max(length_cm, width_cm, height_cm)
    target_max_units = 9.0  # scene units
    units_per_cm = target_max_units / max_dim

    L = length_cm * units_per_cm
    W = width_cm * units_per_cm
    H = height_cm * units_per_cm
    return L, W, H, units_per_cm


def _draw_axis(origin: vector, axis_vec: vector, axis_color, name: str):
    arrow(pos=origin, axis=axis_vec, color=axis_color, shaftwidth=0.06)
    label(pos=origin + axis_vec * 1.05, text=name, box=False, opacity=0, color=axis_color, height=14)


def _dim_line(p1: vector, p2: vector, line_color=color.white):
    """
    Draw a dimension line with end markers + a centered label.
    Returns (line_cyl, end1, end2)
    """
    axis = p2 - p1
    length = (axis.x**2 + axis.y**2 + axis.z**2) ** 0.5
    if length <= 1e-9:
        return None, None, None

    # main line
    line = cylinder(pos=p1, axis=axis, radius=0.02, color=line_color, opacity=0.9)

    # end markers
    end_r = 0.06
    e1 = sphere(pos=p1, radius=end_r, color=line_color, opacity=0.9)
    e2 = sphere(pos=p2, radius=end_r, color=line_color, opacity=0.9)

    return line, e1, e2


def run_viewer(
    title: str,
    length_cm: float,
    width_cm: float,
    height_cm: float,
    weight_kg: float | None = None,
    price_eur: float | None = None,
    currency: str = "EUR",
):
    # Scale to scene units
    L, W, H, units_per_cm = _nice_scale(length_cm, width_cm, height_cm)

    c = canvas(
        title=f"OmniStore 3D – {title}",
        width=960,
        height=620,
        background=color.black,
        center=vector(0, 0, 0),
    )

    # --- "Info panel" (static text) ---
    info_lines = [
        f"<b>{title}</b>",
        f"Dimensions: {length_cm:.1f} × {width_cm:.1f} × {height_cm:.1f} cm",
    ]
    if weight_kg is not None:
        info_lines.append(f"Weight: {weight_kg:.2f} kg")
    if price_eur is not None:
        info_lines.append(f"Price: {price_eur:.2f} {currency}")

    info_lines.append("")
    info_lines.append("Controls: drag=rotate | wheel=zoom | right-drag=pan")
    c.caption = "<br>".join(info_lines)

    # --- Object (centered box) ---
    # VPython size = (x, y, z). We'll map:
    # x = Length, y = Height, z = Width
    obj = box(
        pos=vector(0, 0, 0),
        size=vector(L, H, W),
        color=color.cyan,
        opacity=0.35,
    )

    # --- Floor / base plane ---
    floor_size = max(L, W) * 2.2
    floor_thickness = 0.02
    floor = box(
        pos=vector(0, -H / 2 - floor_thickness / 2, 0),
        size=vector(floor_size, floor_thickness, floor_size),
        color=vector(0.15, 0.18, 0.25),  # dark bluish
        opacity=0.45,
    )

    # --- Axes ---
    axis_len = max(L, W, H) * 0.9
    _draw_axis(vector(0, 0, 0), vector(axis_len, 0, 0), color.red, "X (Length)")
    _draw_axis(vector(0, 0, 0), vector(0, axis_len, 0), color.green, "Y (Height)")
    _draw_axis(vector(0, 0, 0), vector(0, 0, axis_len), color.blue, "Z (Width)")

    # --- Dimension lines around the box ---
    pad = max(L, W, H) * 0.22

    # Length line (X) under the object
    p1_L = vector(-L/2, -H/2 - pad, -W/2 - pad)
    p2_L = vector(L/2,  -H/2 - pad, -W/2 - pad)
    _dim_line(p1_L, p2_L)
    label(pos=(p1_L + p2_L) * 0.5, text=f"L = {length_cm:.1f} cm", box=False, opacity=0, color=color.white, height=14)

    # Width line (Z) under the object
    p1_W = vector(-L/2 - pad, -H/2 - pad, -W/2)
    p2_W = vector(-L/2 - pad, -H/2 - pad,  W/2)
    _dim_line(p1_W, p2_W)
    label(pos=(p1_W + p2_W) * 0.5, text=f"W = {width_cm:.1f} cm", box=False, opacity=0, color=color.white, height=14)

    # Height line (Y) next to the object
    p1_H = vector(-L/2 - pad, -H/2, -W/2 - pad)
    p2_H = vector(-L/2 - pad,  H/2, -W/2 - pad)
    _dim_line(p1_H, p2_H)
    label(pos=(p1_H + p2_H) * 0.5, text=f"H = {height_cm:.1f} cm", box=False, opacity=0, color=color.white, height=14)

    # Camera defaults
    c.autoscale = False
    c.range = max(L, W, H) * 1.35

    # Keep alive
    while True:
        rate(60)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--length", type=float, required=True)
    p.add_argument("--width", type=float, required=True)
    p.add_argument("--height", type=float, required=True)
    p.add_argument("--weight", type=float, default=None)
    p.add_argument("--price", type=float, default=None)
    p.add_argument("--currency", type=str, default="EUR")
    args = p.parse_args()

    run_viewer(
        title=args.title,
        length_cm=args.length,
        width_cm=args.width,
        height_cm=args.height,
        weight_kg=args.weight,
        price_eur=args.price,
        currency=args.currency,
    )


if __name__ == "__main__":
    main()
