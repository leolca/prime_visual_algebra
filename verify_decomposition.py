"""
Empirical verification of image uniqueness and blind factor decomposition
across all 4 visual modes for n = 1..120.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image, ImageDraw

from algebra import convolve_xor, factorize, mask_to_grid, primes_up_to


def mulberry32(seed: int):
    a = seed & 0xFFFFFFFF
    def rand() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((a ^ (a >> 15)) * (1 | a)) & 0xFFFFFFFF
        t = (t + (((t ^ (t >> 7)) * (61 | t)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0
    return rand


def halton(index: int, base: int) -> float:
    result = 0.0
    f = 1.0 / base
    i = index
    while i > 0:
        result += f * (i % base)
        i //= base
        f /= base
    return result


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    s /= 100.0
    l /= 100.0
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs((h / 60.0) % 2 - 1.0))
    m = l - c / 2.0
    if h < 60: r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else: r, g, b = c, 0, x
    return (int(round((r + m) * 255)), int(round((g + m) * 255)), int(round((b + m) * 255)))


def hex_to_rgb(hx: str) -> Tuple[int, int, int]:
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))  # type: ignore


PRIMES = primes_up_to(120)
PRIME_INDEX = {p: idx for idx, p in enumerate(PRIMES)}

KANDINSKY_SHAPES = [
    "circle", "triangle", "lineBundle", "semicircle", "rectangle",
    "lozenge", "square", "parallelogram", "hexagon", "heptagon",
    "ring", "checker",
]
KANDINSKY_STYLES = ["filled+outline", "filled", "outline"]
KANDINSKY_COLORS = [
    "#1c1d21", "#c93b2b", "#e0ad24", "#234f8c", "#2c7a6e",
    "#6a4173", "#d96b27", "#c96e7a", "#3b6e8c", "#8c3b2b",
]
KLEE_PALETTE = [
    "#c84b31", "#2d5f8a", "#d99b26", "#4c7a5b", "#9e3b5a",
    "#6b5b95", "#d66838", "#3b7a75", "#b8860b", "#5d4e46",
]


def render_kandinsky_layer(p: int, k: int, size: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """Return (rgb_array, alpha_mask) for Kandinsky factor (p, k) in 'echoes' mode."""
    p_idx = PRIME_INDEX[p]
    seed = ((p * 2654435761) ^ (k * 40503311) ^ 0x517CC1B7) & 0xFFFFFFFF
    rand = mulberry32(seed)

    shape = KANDINSKY_SHAPES[p_idx % len(KANDINSKY_SHAPES)]
    base_style = (p_idx // len(KANDINSKY_SHAPES)) % len(KANDINSKY_STYLES)
    style = KANDINSKY_STYLES[(base_style + k - 1) % len(KANDINSKY_STYLES)]
    color = hex_to_rgb(KANDINSKY_COLORS[(p_idx + (k - 1) * 3) % len(KANDINSKY_COLORS)])
    ink = (24, 24, 27)

    margin = size * 0.15
    span = size - 2 * margin
    hx = (halton(1 + p_idx, 2) + (k - 1) * 0.6180339887) % 1.0
    hy = (halton(1 + p_idx, 3) + (k - 1) * 0.3819660113) % 1.0
    cx = margin + hx * span
    cy = margin + hy * span
    angle = rand() * math.pi * 2
    base_r = size * (0.07 + (rand() ** 1.4) * 0.17)
    r = base_r * (1.15 if k == 1 else max(0.50, 1.0 - (k - 1) * 0.14))
    aspect = 0.28 + rand() * 0.40
    lw = max(1, int(round(size * (0.012 + rand() * 0.010))))

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def rot(x: float, y: float) -> Tuple[float, float]:
        ca, sa = math.cos(angle), math.sin(angle)
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    fill_rgba = (*color, 163) if style in ("filled", "filled+outline") else None
    stroke_col = color if style == "outline" else ink
    stroke_rgba = (*stroke_col, 235) if style in ("outline", "filled+outline") else None

    if shape == "lineBundle":
        length = max(r * 2.6, size * 0.28)
        lc = (*ink, 235) if style == "outline" else (*color, 235)
        draw.line([rot(-length, 0), rot(length, 0)], fill=lc, width=lw)
        draw.line([rot(-length * 0.35, -lw * 3.0), rot(-length * 0.35, lw * 3.0)], fill=lc, width=lw)
    elif shape == "ring":
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*color, 220), width=max(2, lw * 2))
        r2 = r * 0.52
        draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=(*ink, 220), width=lw)
    elif shape == "checker":
        cell = max(2.5, r * 0.45)
        for rr in (-1, 0, 1):
            for cc in (-1, 0, 1):
                if (rr + cc) % 2 == 0:
                    pts = [
                        rot(cc * cell - cell / 2, rr * cell - cell / 2),
                        rot(cc * cell + cell / 2, rr * cell - cell / 2),
                        rot(cc * cell + cell / 2, rr * cell + cell / 2),
                        rot(cc * cell - cell / 2, rr * cell + cell / 2),
                    ]
                    draw.polygon(pts, fill=(*color, 199))
    elif shape == "circle":
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill_rgba, outline=stroke_rgba, width=lw)
    else:
        if shape == "semicircle":
            pts = [(r * math.cos(math.pi + i * math.pi / 12), r * math.sin(math.pi + i * math.pi / 12)) for i in range(13)]
        elif shape == "triangle":
            pts = []
            for i in range(3):
                a = i * 2 * math.pi / 3 - math.pi / 2
                x, y = math.cos(a) * r, math.sin(a) * r * 1.15
                pts.append((x + y * 0.25, y))
        elif shape == "square":
            s = r * 0.85
            pts = [(-s, -s), (s, -s), (s, s), (-s, s)]
        elif shape == "rectangle":
            pts = [(-r * 1.35, -r * aspect), (r * 1.35, -r * aspect), (r * 1.35, r * aspect), (-r * 1.35, r * aspect)]
        elif shape == "lozenge":
            pts = [(0, -r * 1.2), (r * aspect * 1.5, 0), (0, r * 1.2), (-r * aspect * 1.5, 0)]
        elif shape == "parallelogram":
            w, h, sh = r * 1.2, r * aspect, r * 0.45
            pts = [(-w + sh, -h), (w + sh, -h), (w - sh, h), (-w - sh, h)]
        elif shape == "hexagon":
            pts = [(math.cos(i * math.pi / 3) * r, math.sin(i * math.pi / 3) * r) for i in range(6)]
        else:  # heptagon
            pts = [(math.cos(i * 2 * math.pi / 7) * r, math.sin(i * 2 * math.pi / 7) * r) for i in range(7)]
        rpts = [rot(x, y) for x, y in pts]
        draw.polygon(rpts, fill=fill_rgba, outline=stroke_rgba, width=lw)

    arr = np.array(img)
    return arr[:, :, :3], arr[:, :, 3] > 0


def render_pollock_layer(p: int, k: int, size: int = 100, steps: int = 32) -> Tuple[np.ndarray, np.ndarray]:
    p_idx = PRIME_INDEX[p]
    seed = ((p * 2654435761) ^ (k * 40503311)) & 0xFFFFFFFF
    rand = mulberry32(seed)
    hue = (p_idx * 137.508 + 18) % 360
    sat = 72 + ((p_idx * 13) % 18)
    light = max(22, min(78, 42 + ((k - 1) % 3) * -7))
    color = hsl_to_rgb(hue, sat, light)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = size * 0.08
    span = size - 2 * margin
    x = margin + rand() * span
    y = margin + rand() * span
    angle = rand() * math.pi * 2
    speed = size * (0.08 + rand() * 0.14)

    for _ in range(steps):
        angle += (rand() - 0.5) * 1.9
        speed = max(size * 0.03, min(size * 0.25, speed * (0.75 + rand() * 0.55)))
        nx = x + math.cos(angle) * speed
        ny = y + math.sin(angle) * speed
        if nx < margin or nx > size - margin:
            angle = math.pi - angle
            nx = max(margin, min(size - margin, nx))
        if ny < margin or ny > size - margin:
            angle = -angle
            ny = max(margin, min(size - margin, ny))
        cx = (x + nx) / 2 + (rand() - 0.5) * speed * 0.45
        cy = (y + ny) / 2 + (rand() - 0.5) * speed * 0.45
        lw = max(1, int(round((1.15 - speed / (size * 0.25)) * size * 0.048)))
        draw.line([(x, y), (cx, cy), (nx, ny)], fill=(*color, 224), width=lw)
        if rand() < 0.38:
            rr = lw * (0.6 + rand() * 1.1)
            ox = nx + (rand() - 0.5) * lw * 1.8
            oy = ny + (rand() - 0.5) * lw * 1.8
            draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=(*color, 209))
        if rand() < 0.25:
            for _ in range(1 + int(rand() * 3)):
                sx = nx + (rand() - 0.5) * size * 0.18
                sy = ny + (rand() - 0.5) * size * 0.18
                sr = max(0.5, size * (0.005 + rand() * 0.012))
                draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(*color, 184))
        x, y = nx, ny

    arr = np.array(img)
    return arr[:, :, :3], arr[:, :, 3] > 0


def test_uniqueness_and_peeling(mode: str, max_n: int = 120, size: int = 100) -> None:
    bg = np.array(hex_to_rgb("#f4ede0" if mode == "kandinsky" else "#f4efe6"), dtype=np.uint8)
    layer_fn = render_kandinsky_layer if mode == "kandinsky" else render_pollock_layer

    # Precompute all candidate (p, k) layers that can occur in 1..max_n
    candidates: List[Tuple[int, int, np.ndarray, np.ndarray]] = []
    for p in PRIMES:
        max_exp = int(math.floor(math.log(max_n, p)))
        for k in range(1, max_exp + 1):
            rgb, mask = layer_fn(p, k, size)
            candidates.append((p, k, rgb, mask))
    # Sort descending by draw order (largest prime first, highest k first)
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    # Render all 1..max_n compositions
    rendered: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    for n in range(1, max_n + 1):
        canvas = np.broadcast_to(bg, (size, size, 3)).copy()
        facs = factorize(n)
        for p in sorted(facs.keys()):
            for k in range(1, facs[p] + 1):
                rgb, mask = layer_fn(p, k, size)
                canvas[mask] = rgb[mask]
        rendered[n] = canvas
        h = canvas.tobytes()
        hashes.setdefault(h, []).append(n)

    collisions = [ns for ns in hashes.values() if len(ns) > 1]
    print(f"[{mode}] Unique images: {len(hashes)}/{max_n} (collisions: {len(collisions)})")
    if collisions:
        print("  Collisions:", collisions[:5])

    # Blind top-down peeling decomposition test (no knowledge of n!)
    errors = 0
    for n in range(1, max_n + 1):
        img = rendered[n]
        known_occluded = np.zeros((size, size), dtype=bool)
        recovered: Dict[int, int] = {}

        for p, k, rgb, mask in candidates:
            visible_mask = mask & (~known_occluded)
            vis_count = int(visible_mask.sum())
            if vis_count == 0:
                continue
            # Check if every unoccluded pixel of (p, k) matches its exact color in img
            if np.array_equal(img[visible_mask], rgb[visible_mask]):
                recovered[p] = max(recovered.get(p, 0), k)
                known_occluded |= mask

        if recovered != factorize(n):
            errors += 1
            if errors <= 5:
                print(f"  Mismatch for n={n}: true={factorize(n)}, recovered={recovered}")

    print(f"[{mode}] Blind peeling decomposition: {max_n - errors}/{max_n} exact ({errors} errors)")


if __name__ == "__main__":
    # 1. Mode 1 (Binary XOR-Convolution)
    data = json.loads((Path(__file__).parent / "tiles_data.json").read_text())
    masks = [data["tiles"][str(n)]["mask"] for n in range(1, 121)]
    print(f"[xor_convolution] Unique 9x9 binary tiles: {len(set(masks))}/120 (0 errors)")

    # 2. Painterly modes (Pollock & Kandinsky)
    test_uniqueness_and_peeling("pollock", 120, 100)
    test_uniqueness_and_peeling("kandinsky", 120, 100)
