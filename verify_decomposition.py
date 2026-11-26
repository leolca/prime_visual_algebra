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


def klee_color_rgb(p: int) -> Tuple[int, int, int]:
    idx = PRIME_INDEX[p]
    if idx < len(KLEE_PALETTE):
        return hex_to_rgb(KLEE_PALETTE[idx])
    hue = (idx * 137.508 + 24) % 360
    return hsl_to_rgb(hue, 54.0, 46.0)


def render_klee_attenuation(p: int, exp: int, size: int = 100) -> np.ndarray:
    """Return float32 multiplicative attenuation array of shape (size, size, 3) in (0, 1]."""
    p_idx = PRIME_INDEX[p]
    seed = ((p * 2654435761) ^ 0x9E3779B9) & 0xFFFFFFFF
    rand = mulberry32(seed)
    color = np.array(klee_color_rgb(p), dtype=np.float32) / 255.0

    margin = size * 0.08
    span = size - 2 * margin
    stroke_w = size * (0.09 + rand() * 0.09)
    jump = stroke_w * 1.3
    horizontal = (p_idx % 2 == 0)

    pos = margin + rand() * span
    track = margin + stroke_w * 0.5 + rand() * max(1.0, span - stroke_w)
    remaining = exp * span * 0.95

    atten = np.ones((size, size, 3), dtype=np.float32)
    guard = 0
    while remaining > 0.5 and guard < 40:
        guard += 1
        avail = (margin + span) - pos
        seg_len = min(remaining, max(2.0, avail))

        for w_idx in range(2):
            wobble = lambda: (rand() - 0.5) * stroke_w * 0.14
            half_w = stroke_w * (0.48 + w_idx * 0.06)
            pts: List[Tuple[float, float]] = []
            steps = 5
            if horizontal:
                for i in range(steps + 1):
                    t = i / steps
                    pts.append((pos + seg_len * t + wobble() * 0.3, track - half_w + wobble()))
                for i in range(steps, -1, -1):
                    t = i / steps
                    pts.append((pos + seg_len * t + wobble() * 0.3, track + half_w + wobble()))
            else:
                for i in range(steps + 1):
                    t = i / steps
                    pts.append((track - half_w + wobble(), pos + seg_len * t + wobble() * 0.3))
                for i in range(steps, -1, -1):
                    t = i / steps
                    pts.append((track + half_w + wobble(), pos + seg_len * t + wobble() * 0.3))

            mask_img = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask_img).polygon(pts, fill=255)
            m = np.array(mask_img) > 0
            alpha = 0.42 if w_idx == 0 else 0.28
            atten[m] *= (1.0 - alpha) + alpha * color

        remaining -= seg_len
        if remaining > 0.5:
            pos = margin
            track += jump
            if track > margin + span - stroke_w * 0.3:
                track = margin + ((track - margin) % max(stroke_w, span - stroke_w * 0.5))

    return atten


def test_klee_uniqueness_and_peeling(max_n: int = 120, size: int = 100) -> None:
    bg = np.array(hex_to_rgb("#f6f0e2"), dtype=np.float32)

    # Precompute attenuation for every (p, e)
    attens: Dict[Tuple[int, int], np.ndarray] = {}
    for p in PRIMES:
        max_exp = int(math.floor(math.log(max_n, p)))
        for e in range(1, max_exp + 1):
            attens[(p, e)] = render_klee_attenuation(p, e, size)

    # Render all 1..max_n
    rendered: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    for n in range(1, max_n + 1):
        canvas = np.broadcast_to(bg, (size, size, 3)).copy()
        for p, e in sorted(factorize(n).items()):
            canvas *= attens[(p, e)]
        img_u8 = np.clip(np.round(canvas), 0, 255).astype(np.uint8)
        rendered[n] = img_u8
        hashes.setdefault(img_u8.tobytes(), []).append(n)

    collisions = [ns for ns in hashes.values() if len(ns) > 1]
    print(f"[klee] Unique images: {len(hashes)}/{max_n} (collisions: {len(collisions)})")

    # Blind multiplicative glaze peeling:
    # Check each prime p from largest to smallest, and largest exponent e first.
    # Since multiply only darkens (atten <= 1), if (p, e) is present, every pixel of (p, e)
    # must satisfy residual <= bg * atten(p, e) + tolerance (for uint8 rounding).
    # To avoid false positives from overlap of other primes, we also require that
    # peeling (p, e) leaves residual <= bg + tolerance everywhere, and we prefer the
    # highest e whose unoccluded/darkened footprint fits cleanly.
    errors = 0
    for n in range(1, max_n + 1):
        residual = rendered[n].astype(np.float32) / bg  # in (0, 1]
        recovered: Dict[int, int] = {}
        for p in sorted(PRIMES, reverse=True):
            max_exp = int(math.floor(math.log(max_n, p)))
            for e in range(max_exp, 0, -1):
                att = attens[(p, e)]
                mask = np.any(att < 0.999, axis=2)
                if not np.any(mask):
                    continue
                # Every pixel in (p, e)'s footprint must be at least as dark as att (within uint8 rounding)
                # i.e. residual <= att + 2.5 / bg_min
                if np.all(residual[mask] <= att[mask] + 0.015):
                    recovered[p] = e
                    residual[mask] = np.minimum(1.0, residual[mask] / np.maximum(att[mask], 1e-4))
                    break

        if recovered != factorize(n):
            errors += 1
            if errors <= 5:
                print(f"  Klee mismatch for n={n}: true={factorize(n)}, recovered={recovered}")

    print(f"[klee] Blind multiplicative peeling: {max_n - errors}/{max_n} exact ({errors} errors)")


def test_pollock_glaze_homomorphism(max_n: int = 120, size: int = 100) -> None:
    """Verify pixel-level homomorphism, uniqueness, and multiplicative peeling for Pollock Glaze mode."""
    bg = np.array(hex_to_rgb("#f4efe6"), dtype=np.float32)
    alpha = 0.45 * 0.88  # base alpha * stroke alpha

    prime_attens: Dict[int, np.ndarray] = {}
    for p in PRIMES:
        rgb, mask = render_pollock_layer(p, 1, size=size, steps=32)
        att = np.ones((size, size, 3), dtype=np.float32)
        col = rgb.astype(np.float32) / 255.0
        att[mask] = (1.0 - alpha) + alpha * col[mask]
        prime_attens[p] = att

    # Render exact float attenuation for each n = 1..max_n
    rendered_float: Dict[int, np.ndarray] = {}
    rendered_u8: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    for n in range(1, max_n + 1):
        att = np.ones((size, size, 3), dtype=np.float32)
        for p, e in factorize(n).items():
            att *= (prime_attens[p] ** e)
        rendered_float[n] = att
        u8 = np.clip(np.round(bg * att), 0, 255).astype(np.uint8)
        rendered_u8[n] = u8
        hashes.setdefault(u8.tobytes(), []).append(n)

    # Check pixel-level homomorphism: I(a*b) == bg * (I(a)/bg) * (I(b)/bg)
    hom_errors = 0
    for a in range(1, max_n + 1):
        for b in range(a, max_n // a + 1):
            prod = rendered_float[a] * rendered_float[b]
            if not np.allclose(prod, rendered_float[a * b], atol=1e-5):
                hom_errors += 1

    # Blind multiplicative peeling on uint8 renders
    peel_errors = 0
    for n in range(1, max_n + 1):
        residual = rendered_u8[n].astype(np.float32) / bg
        recovered: Dict[int, int] = {}
        for p in sorted(PRIMES, reverse=True):
            att_p = prime_attens[p]
            mask = np.any(att_p < 0.999, axis=2)
            if not np.any(mask):
                continue
            max_exp = int(math.floor(math.log(max_n, p)))
            for e in range(max_exp, 0, -1):
                att_pe = att_p ** e
                if np.all(residual[mask] <= att_pe[mask] + 0.015):
                    recovered[p] = e
                    residual[mask] = np.minimum(1.0, residual[mask] / np.maximum(att_pe[mask], 1e-4))
                    break
        if recovered != factorize(n):
            peel_errors += 1

    print(f"[pollock_glaze] Pixel homomorphism errors: {hom_errors}")
    print(f"[pollock_glaze] Unique images: {len(hashes)}/{max_n}")
    print(f"[pollock_glaze] Blind multiplicative peeling: {max_n - peel_errors}/{max_n} exact ({peel_errors} errors)")


def test_pollock_trajectory_homomorphism(max_n: int = 120, size: int = 100) -> None:
    """Verify vector-space homomorphism gamma_{a*b} = gamma_a + gamma_b and image uniqueness."""
    def prime_modes(p: int):
        seed = ((p * 2654435761) ^ 0x7F4A7C15) & 0xFFFFFFFF
        rand = mulberry32(seed)
        modes = []
        for m in range(1, 7):
            amp = 0.13 / math.sqrt(m)
            modes.append((
                1 + int(rand() * 7),
                1 + int(rand() * 7),
                rand() * math.pi * 2,
                rand() * math.pi * 2,
                amp * (0.6 + 0.8 * rand()),
                amp * (0.6 + 0.8 * rand()),
            ))
        return modes

    num_pts = 64
    ts = np.linspace(0.0, 1.0, num_pts + 1)
    prime_curves: Dict[int, np.ndarray] = {}
    for p in PRIMES:
        modes = prime_modes(p)
        dx = np.zeros_like(ts)
        dy = np.zeros_like(ts)
        for fx, fy, px, py, ax, ay in modes:
            dx += ax * np.cos(2 * math.pi * fx * ts + px)
            dy += ay * np.sin(2 * math.pi * fy * ts + py)
        prime_curves[p] = np.stack([dx, dy], axis=1)

    curves: Dict[int, np.ndarray] = {}
    rendered_imgs: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    bg = hex_to_rgb("#f4efe6")

    def render_from_facs(facs: Dict[int, int]) -> np.ndarray:
        gamma = np.zeros((num_pts + 1, 2), dtype=np.float64)
        for p, e in facs.items():
            gamma += e * prime_curves[p]
        img = Image.new("RGB", (size, size), bg)
        draw = ImageDraw.Draw(img)
        if facs:
            sx = sum(e * math.cos(math.radians((PRIME_INDEX[p] * 137.508 + 18) % 360)) for p, e in facs.items())
            sy = sum(e * math.sin(math.radians((PRIME_INDEX[p] * 137.508 + 18) % 360)) for p, e in facs.items())
            hue = (math.degrees(math.atan2(sy, sx)) + 360) % 360
            col = hsl_to_rgb(hue, 74.0, 40.0)
            margin = size * 0.06
            span = size - 2 * margin
            pts = [
                (margin + (((0.5 + x) % 1.0) * span), margin + (((0.5 + y) % 1.0) * span))
                for x, y in gamma
            ]
            rand_drip = mulberry32(1234567)
            for i in range(len(pts) - 1):
                dist = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                if dist <= span * 0.45:
                    u_sp = min(1.0, dist / (size * 0.10))
                    lw = max(1, int(round((1.15 - u_sp) * (size * 0.036))))
                    draw.line([pts[i], pts[i + 1]], fill=col, width=lw)
                    if rand_drip() < 0.35 - 0.28 * u_sp:
                        rr = max(1.0, lw * (0.55 + rand_drip() * 0.45))
                        ox, oy = pts[i + 1][0] + (rand_drip() - 0.5) * lw, pts[i + 1][1] + (rand_drip() - 0.5) * lw
                        draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=col)
                    if rand_drip() < 0.05 + 0.22 * u_sp:
                        for _ in range(1 + int(rand_drip() * 2)):
                            sx = pts[i + 1][0] + (rand_drip() - 0.5) * size * 0.12
                            sy = pts[i + 1][1] + (rand_drip() - 0.5) * size * 0.12
                            sr = max(0.5, size * (0.004 + rand_drip() * 0.008))
                            draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=col)
        return np.array(img)

    for n in range(1, max_n + 1):
        facs = factorize(n)
        gamma = np.zeros((num_pts + 1, 2), dtype=np.float64)
        for p, e in facs.items():
            gamma += e * prime_curves[p]
        curves[n] = gamma
        arr = render_from_facs(facs)
        rendered_imgs[n] = arr
        hashes.setdefault(arr.tobytes(), []).append(n)

    hom_errors = 0
    for a in range(1, max_n + 1):
        for b in range(a, max_n // a + 1):
            if not np.allclose((curves[a] + curves[b]) % 1.0, curves[a * b] % 1.0, atol=1e-12):
                hom_errors += 1

    # Blind prime-spectrum DFS over products <= max_n (no composite lookup table)
    def decompose_traj(target_bytes: bytes) -> Dict[int, int] | None:
        if target_bytes == render_from_facs({}).tobytes():
            return {}
        def search(idx: int, cur_n: int, cur_facs: Dict[int, int]) -> Dict[int, int] | None:
            if cur_n > 1 and render_from_facs(cur_facs).tobytes() == target_bytes:
                return dict(cur_facs)
            for i in range(idx, len(PRIMES)):
                p = PRIMES[i]
                if cur_n * p > max_n:
                    break
                cur_facs[p] = cur_facs.get(p, 0) + 1
                res = search(i, cur_n * p, cur_facs)
                if res is not None:
                    return res
                if cur_facs[p] == 1:
                    del cur_facs[p]
                else:
                    cur_facs[p] -= 1
            return None
        return search(0, 1, {})

    rec_errors = 0
    for n in range(1, max_n + 1):
        if decompose_traj(rendered_imgs[n].tobytes()) != factorize(n):
            rec_errors += 1

    print(f"[pollock_trajectory] Vector homomorphism errors: {hom_errors}")
    print(f"[pollock_trajectory] Unique images: {len(hashes)}/{max_n}")
    print(f"[pollock_trajectory] Blind prime-spectrum recovery: {max_n - rec_errors}/{max_n} exact ({rec_errors} errors)")


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
        u_t = max(0.0, min(1.0, (speed - size * 0.03) / (size * 0.22)))
        p_pool = 0.58 - 0.40 * u_t
        p_spray = 0.08 + 0.34 * u_t
        if rand() < p_pool:
            rr = lw * (0.5 + rand() * 0.65)
            ox = nx + (rand() - 0.5) * lw * 1.8
            oy = ny + (rand() - 0.5) * lw * 1.8
            draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=(*color, 209))
        if rand() < p_spray:
            for _ in range(1 + int(rand() * 3)):
                sx = nx + (rand() - 0.5) * size * 0.18
                sy = ny + (rand() - 0.5) * size * 0.18
                sr = max(0.5, size * (0.005 + rand() * 0.012))
                draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(*color, 184))
        x, y = nx, ny

    arr = np.array(img)
    return arr[:, :, :3], arr[:, :, 3] > 0


def klee_color_rgb(p: int) -> Tuple[int, int, int]:
    idx = PRIME_INDEX[p]
    if idx < len(KLEE_PALETTE):
        return hex_to_rgb(KLEE_PALETTE[idx])
    hue = (idx * 137.508 + 24) % 360
    return hsl_to_rgb(hue, 54.0, 46.0)


def render_klee_attenuation(p: int, exp: int, size: int = 100) -> np.ndarray:
    """Return float32 multiplicative attenuation array of shape (size, size, 3) in (0, 1]."""
    p_idx = PRIME_INDEX[p]
    seed = ((p * 2654435761) ^ 0x9E3779B9) & 0xFFFFFFFF
    rand = mulberry32(seed)
    color = np.array(klee_color_rgb(p), dtype=np.float32) / 255.0

    margin = size * 0.08
    span = size - 2 * margin
    stroke_w = size * (0.09 + rand() * 0.09)
    jump = stroke_w * 1.3
    horizontal = (p_idx % 2 == 0)

    pos = margin + rand() * span
    track = margin + stroke_w * 0.5 + rand() * max(1.0, span - stroke_w)
    remaining = exp * span * 0.95

    atten = np.ones((size, size, 3), dtype=np.float32)
    guard = 0
    while remaining > 0.5 and guard < 40:
        guard += 1
        avail = (margin + span) - pos
        seg_len = min(remaining, max(2.0, avail))

        for w_idx in range(2):
            wobble = lambda: (rand() - 0.5) * stroke_w * 0.14
            half_w = stroke_w * (0.48 + w_idx * 0.06)
            pts: List[Tuple[float, float]] = []
            steps = 5
            if horizontal:
                for i in range(steps + 1):
                    t = i / steps
                    pts.append((pos + seg_len * t + wobble() * 0.3, track - half_w + wobble()))
                for i in range(steps, -1, -1):
                    t = i / steps
                    pts.append((pos + seg_len * t + wobble() * 0.3, track + half_w + wobble()))
            else:
                for i in range(steps + 1):
                    t = i / steps
                    pts.append((track - half_w + wobble(), pos + seg_len * t + wobble() * 0.3))
                for i in range(steps, -1, -1):
                    t = i / steps
                    pts.append((track + half_w + wobble(), pos + seg_len * t + wobble() * 0.3))

            mask_img = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask_img).polygon(pts, fill=255)
            m = np.array(mask_img) > 0
            alpha = 0.42 if w_idx == 0 else 0.28
            atten[m] *= (1.0 - alpha) + alpha * color

        remaining -= seg_len
        if remaining > 0.5:
            pos = margin
            track += jump
            if track > margin + span - stroke_w * 0.3:
                track = margin + ((track - margin) % max(stroke_w, span - stroke_w * 0.5))

    return atten


def test_klee_uniqueness_and_peeling(max_n: int = 120, size: int = 100) -> None:
    bg = np.array(hex_to_rgb("#f6f0e2"), dtype=np.float32)

    # Precompute attenuation for every (p, e)
    attens: Dict[Tuple[int, int], np.ndarray] = {}
    for p in PRIMES:
        max_exp = int(math.floor(math.log(max_n, p)))
        for e in range(1, max_exp + 1):
            attens[(p, e)] = render_klee_attenuation(p, e, size)

    # Render all 1..max_n
    rendered: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    for n in range(1, max_n + 1):
        canvas = np.broadcast_to(bg, (size, size, 3)).copy()
        for p, e in sorted(factorize(n).items()):
            canvas *= attens[(p, e)]
        img_u8 = np.clip(np.round(canvas), 0, 255).astype(np.uint8)
        rendered[n] = img_u8
        hashes.setdefault(img_u8.tobytes(), []).append(n)

    collisions = [ns for ns in hashes.values() if len(ns) > 1]
    print(f"[klee] Unique images: {len(hashes)}/{max_n} (collisions: {len(collisions)})")

    # Blind multiplicative glaze peeling:
    # Check each prime p from largest to smallest, and largest exponent e first.
    # Since multiply only darkens (atten <= 1), if (p, e) is present, every pixel of (p, e)
    # must satisfy residual <= bg * atten(p, e) + tolerance (for uint8 rounding).
    # To avoid false positives from overlap of other primes, we also require that
    # peeling (p, e) leaves residual <= bg + tolerance everywhere, and we prefer the
    # highest e whose unoccluded/darkened footprint fits cleanly.
    errors = 0
    for n in range(1, max_n + 1):
        residual = rendered[n].astype(np.float32) / bg  # in (0, 1]
        recovered: Dict[int, int] = {}
        for p in sorted(PRIMES, reverse=True):
            max_exp = int(math.floor(math.log(max_n, p)))
            for e in range(max_exp, 0, -1):
                att = attens[(p, e)]
                mask = np.any(att < 0.999, axis=2)
                if not np.any(mask):
                    continue
                # Every pixel in (p, e)'s footprint must be at least as dark as att (within uint8 rounding)
                # i.e. residual <= att + 2.5 / bg_min
                if np.all(residual[mask] <= att[mask] + 0.015):
                    recovered[p] = e
                    residual[mask] = np.minimum(1.0, residual[mask] / np.maximum(att[mask], 1e-4))
                    break

        if recovered != factorize(n):
            errors += 1
            if errors <= 5:
                print(f"  Klee mismatch for n={n}: true={factorize(n)}, recovered={recovered}")

    print(f"[klee] Blind multiplicative peeling: {max_n - errors}/{max_n} exact ({errors} errors)")


def test_pollock_glaze_homomorphism(max_n: int = 120, size: int = 100) -> None:
    """Verify pixel-level homomorphism, uniqueness, and multiplicative peeling for Pollock Glaze mode."""
    bg = np.array(hex_to_rgb("#f4efe6"), dtype=np.float32)
    alpha = 0.45 * 0.88  # base alpha * stroke alpha

    prime_attens: Dict[int, np.ndarray] = {}
    for p in PRIMES:
        rgb, mask = render_pollock_layer(p, 1, size=size, steps=32)
        att = np.ones((size, size, 3), dtype=np.float32)
        col = rgb.astype(np.float32) / 255.0
        att[mask] = (1.0 - alpha) + alpha * col[mask]
        prime_attens[p] = att

    # Render exact float attenuation for each n = 1..max_n
    rendered_float: Dict[int, np.ndarray] = {}
    rendered_u8: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    for n in range(1, max_n + 1):
        att = np.ones((size, size, 3), dtype=np.float32)
        for p, e in factorize(n).items():
            att *= (prime_attens[p] ** e)
        rendered_float[n] = att
        u8 = np.clip(np.round(bg * att), 0, 255).astype(np.uint8)
        rendered_u8[n] = u8
        hashes.setdefault(u8.tobytes(), []).append(n)

    # Check pixel-level homomorphism: I(a*b) == bg * (I(a)/bg) * (I(b)/bg)
    hom_errors = 0
    for a in range(1, max_n + 1):
        for b in range(a, max_n // a + 1):
            prod = rendered_float[a] * rendered_float[b]
            if not np.allclose(prod, rendered_float[a * b], atol=1e-5):
                hom_errors += 1

    # Blind multiplicative peeling on uint8 renders
    peel_errors = 0
    for n in range(1, max_n + 1):
        residual = rendered_u8[n].astype(np.float32) / bg
        recovered: Dict[int, int] = {}
        for p in sorted(PRIMES, reverse=True):
            att_p = prime_attens[p]
            mask = np.any(att_p < 0.999, axis=2)
            if not np.any(mask):
                continue
            max_exp = int(math.floor(math.log(max_n, p)))
            for e in range(max_exp, 0, -1):
                att_pe = att_p ** e
                if np.all(residual[mask] <= att_pe[mask] + 0.015):
                    recovered[p] = e
                    residual[mask] = np.minimum(1.0, residual[mask] / np.maximum(att_pe[mask], 1e-4))
                    break
        if recovered != factorize(n):
            peel_errors += 1

    print(f"[pollock_glaze] Pixel homomorphism errors: {hom_errors}")
    print(f"[pollock_glaze] Unique images: {len(hashes)}/{max_n}")
    print(f"[pollock_glaze] Blind multiplicative peeling: {max_n - peel_errors}/{max_n} exact ({peel_errors} errors)")


def test_pollock_trajectory_homomorphism(max_n: int = 120, size: int = 100) -> None:
    """Verify vector-space homomorphism gamma_{a*b} = gamma_a + gamma_b and image uniqueness."""
    def prime_modes(p: int):
        seed = ((p * 2654435761) ^ 0x7F4A7C15) & 0xFFFFFFFF
        rand = mulberry32(seed)
        modes = []
        for m in range(1, 7):
            amp = 0.13 / math.sqrt(m)
            modes.append((
                1 + int(rand() * 7),
                1 + int(rand() * 7),
                rand() * math.pi * 2,
                rand() * math.pi * 2,
                amp * (0.6 + 0.8 * rand()),
                amp * (0.6 + 0.8 * rand()),
            ))
        return modes

    num_pts = 64
    ts = np.linspace(0.0, 1.0, num_pts + 1)
    prime_curves: Dict[int, np.ndarray] = {}
    for p in PRIMES:
        modes = prime_modes(p)
        dx = np.zeros_like(ts)
        dy = np.zeros_like(ts)
        for fx, fy, px, py, ax, ay in modes:
            dx += ax * np.cos(2 * math.pi * fx * ts + px)
            dy += ay * np.sin(2 * math.pi * fy * ts + py)
        prime_curves[p] = np.stack([dx, dy], axis=1)

    curves: Dict[int, np.ndarray] = {}
    rendered_imgs: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    bg = hex_to_rgb("#f4efe6")

    def render_from_facs(facs: Dict[int, int]) -> np.ndarray:
        gamma = np.zeros((num_pts + 1, 2), dtype=np.float64)
        for p, e in facs.items():
            gamma += e * prime_curves[p]
        img = Image.new("RGB", (size, size), bg)
        draw = ImageDraw.Draw(img)
        if facs:
            sx = sum(e * math.cos(math.radians((PRIME_INDEX[p] * 137.508 + 18) % 360)) for p, e in facs.items())
            sy = sum(e * math.sin(math.radians((PRIME_INDEX[p] * 137.508 + 18) % 360)) for p, e in facs.items())
            hue = (math.degrees(math.atan2(sy, sx)) + 360) % 360
            col = hsl_to_rgb(hue, 74.0, 40.0)
            margin = size * 0.06
            span = size - 2 * margin
            pts = [
                (margin + (((0.5 + x) % 1.0) * span), margin + (((0.5 + y) % 1.0) * span))
                for x, y in gamma
            ]
            rand_drip = mulberry32(1234567)
            for i in range(len(pts) - 1):
                dist = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                if dist <= span * 0.45:
                    u_sp = min(1.0, dist / (size * 0.10))
                    lw = max(1, int(round((1.15 - u_sp) * (size * 0.036))))
                    draw.line([pts[i], pts[i + 1]], fill=col, width=lw)
                    if rand_drip() < 0.35 - 0.28 * u_sp:
                        rr = max(1.0, lw * (0.55 + rand_drip() * 0.45))
                        ox, oy = pts[i + 1][0] + (rand_drip() - 0.5) * lw, pts[i + 1][1] + (rand_drip() - 0.5) * lw
                        draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=col)
                    if rand_drip() < 0.05 + 0.22 * u_sp:
                        for _ in range(1 + int(rand_drip() * 2)):
                            sx = pts[i + 1][0] + (rand_drip() - 0.5) * size * 0.12
                            sy = pts[i + 1][1] + (rand_drip() - 0.5) * size * 0.12
                            sr = max(0.5, size * (0.004 + rand_drip() * 0.008))
                            draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=col)
        return np.array(img)

    for n in range(1, max_n + 1):
        facs = factorize(n)
        gamma = np.zeros((num_pts + 1, 2), dtype=np.float64)
        for p, e in facs.items():
            gamma += e * prime_curves[p]
        curves[n] = gamma
        arr = render_from_facs(facs)
        rendered_imgs[n] = arr
        hashes.setdefault(arr.tobytes(), []).append(n)

    hom_errors = 0
    for a in range(1, max_n + 1):
        for b in range(a, max_n // a + 1):
            if not np.allclose((curves[a] + curves[b]) % 1.0, curves[a * b] % 1.0, atol=1e-12):
                hom_errors += 1

    # Blind prime-spectrum DFS over products <= max_n (no composite lookup table)
    def decompose_traj(target_bytes: bytes) -> Dict[int, int] | None:
        if target_bytes == render_from_facs({}).tobytes():
            return {}
        def search(idx: int, cur_n: int, cur_facs: Dict[int, int]) -> Dict[int, int] | None:
            if cur_n > 1 and render_from_facs(cur_facs).tobytes() == target_bytes:
                return dict(cur_facs)
            for i in range(idx, len(PRIMES)):
                p = PRIMES[i]
                if cur_n * p > max_n:
                    break
                cur_facs[p] = cur_facs.get(p, 0) + 1
                res = search(i, cur_n * p, cur_facs)
                if res is not None:
                    return res
                if cur_facs[p] == 1:
                    del cur_facs[p]
                else:
                    cur_facs[p] -= 1
            return None
        return search(0, 1, {})

    rec_errors = 0
    for n in range(1, max_n + 1):
        if decompose_traj(rendered_imgs[n].tobytes()) != factorize(n):
            rec_errors += 1

    print(f"[pollock_trajectory] Vector homomorphism errors: {hom_errors}")
    print(f"[pollock_trajectory] Unique images: {len(hashes)}/{max_n}")
    print(f"[pollock_trajectory] Blind prime-spectrum recovery: {max_n - rec_errors}/{max_n} exact ({rec_errors} errors)")


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

    print(f"[kandinsky] Blind peeling decomposition: {max_n - errors}/{max_n} exact ({errors} errors)")


def test_pollock_extent_peeling(max_n: int = 120, size: int = 100) -> None:
    """Verify uniqueness and blind top-down peeling for Pollock Path Extent (steps = 32 * e)."""
    bg = np.array(hex_to_rgb("#f4efe6"), dtype=np.uint8)
    candidates: List[Tuple[int, int, np.ndarray, np.ndarray]] = []
    for p in PRIMES:
        max_exp = int(math.floor(math.log(max_n, p)))
        for e in range(1, max_exp + 1):
            rgb, mask = render_pollock_layer(p, 1, size=size, steps=32 * e)
            candidates.append((p, e, rgb, mask))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    rendered: Dict[int, np.ndarray] = {}
    hashes: Dict[bytes, List[int]] = {}
    for n in range(1, max_n + 1):
        canvas = np.broadcast_to(bg, (size, size, 3)).copy()
        facs = factorize(n)
        for p in sorted(facs.keys()):
            rgb, mask = render_pollock_layer(p, 1, size=size, steps=32 * facs[p])
            canvas[mask] = rgb[mask]
        rendered[n] = canvas
        hashes.setdefault(canvas.tobytes(), []).append(n)

    errors = 0
    for n in range(1, max_n + 1):
        img = rendered[n]
        known_occluded = np.zeros((size, size), dtype=bool)
        recovered: Dict[int, int] = {}
        for p, e, rgb, mask in candidates:
            if p in recovered:
                continue
            visible_mask = mask & (~known_occluded)
            if not np.any(visible_mask):
                continue
            if np.array_equal(img[visible_mask], rgb[visible_mask]):
                recovered[p] = e
                known_occluded |= mask
        if recovered != factorize(n):
            errors += 1

    print(f"[pollock_extent] Unique images: {len(hashes)}/{max_n}")
    print(f"[pollock_extent] Blind peeling decomposition: {max_n - errors}/{max_n} exact ({errors} errors)")


def decompose_xor_tile(
    target_mask: int,
    prime_tiles: Dict[int, int],
    max_n: int = 120,
    w: int = 9,
    h: int = 9,
) -> Dict[int, int]:
    """
    Blindly decompose an unknown 9x9 binary tile using ONLY the prime basis tiles
    (without a precomputed composite lookup table) over products <= max_n.
    """
    if target_mask == 1:
        return {}
    primes = sorted(prime_tiles.keys())

    def search(idx: int, cur_n: int, cur_mask: int, cur_facs: Dict[int, int]) -> Dict[int, int] | None:
        if cur_mask == target_mask and cur_n > 1:
            return dict(cur_facs)
        for i in range(idx, len(primes)):
            p = primes[i]
            if cur_n * p > max_n:
                break
            next_mask = convolve_xor(cur_mask, prime_tiles[p], w, h)
            cur_facs[p] = cur_facs.get(p, 0) + 1
            res = search(i, cur_n * p, next_mask, cur_facs)
            if res is not None:
                return res
            if cur_facs[p] == 1:
                del cur_facs[p]
            else:
                cur_facs[p] -= 1
        return None

    found = search(0, 1, 1, {})
    if found is None:
        raise ValueError("Could not decompose XOR tile within max_n")
    return found


def decompose_or_grammar_tile(
    target_mask: int,
    or_pp_tiles: Dict[str, int],
    max_n: int = 120,
) -> Dict[int, int]:
    """
    Blindly decompose an unknown 9x9 OR-grammar tile using ONLY the prime-power
    basis motifs {G_{p,e}} over products <= max_n.
    """
    if target_mask == 0:
        return {}
    primes = sorted({int(k.split("^")[0]) for k in or_pp_tiles.keys()})

    def search(idx: int, cur_n: int, cur_mask: int, cur_facs: Dict[int, int]) -> Dict[int, int] | None:
        if cur_mask == target_mask and cur_n > 1:
            return dict(cur_facs)
        for i in range(idx, len(primes)):
            p = primes[i]
            e = 1
            while cur_n * (p ** e) <= max_n:
                pp_mask = or_pp_tiles[f"{p}^{e}"]
                # Pruning: in OR-grammar, every bit of pp_mask must be present in target_mask
                if (pp_mask & target_mask) == pp_mask:
                    cur_facs[p] = e
                    res = search(i + 1, cur_n * (p ** e), cur_mask | pp_mask, cur_facs)
                    if res is not None:
                        return res
                    del cur_facs[p]
                e += 1
        return None

    found = search(0, 1, 0, {})
    if found is None:
        raise ValueError("Could not decompose OR-grammar tile within max_n")
    return found


if __name__ == "__main__":
    # 1a. Mode 1a (Binary XOR-Convolution): uniqueness + blind basis-search decomposition
    data = json.loads((Path(__file__).parent / "tiles_data.json").read_text())
    prime_tiles = {int(p): int(m) for p, m in data["primes"].items()}
    masks = [int(data["tiles"][str(n)]["mask"]) for n in range(1, 121)]
    print(f"[xor_convolution] Unique 9x9 binary tiles: {len(set(masks))}/120")
    xor_errors = 0
    for n in range(1, 121):
        rec = decompose_xor_tile(masks[n - 1], prime_tiles, max_n=120)
        if rec != factorize(n):
            xor_errors += 1
    print(f"[xor_convolution] Blind basis-search decomposition: {120 - xor_errors}/120 exact ({xor_errors} errors)")

    # 1b. Mode 1b (Binary OR-Grammar): uniqueness + blind subset-pruned decomposition
    or_pp_tiles = {k: int(v) for k, v in data["or_pp_tiles"].items()}
    or_masks = [int(data["tiles"][str(n)]["or_mask"]) for n in range(1, 121)]
    print(f"[or_grammar] Unique 9x9 binary tiles: {len(set(or_masks))}/120")
    or_errors = 0
    for n in range(1, 121):
        rec = decompose_or_grammar_tile(or_masks[n - 1], or_pp_tiles, max_n=120)
        if rec != factorize(n):
            or_errors += 1
    print(f"[or_grammar] Blind subset-pruned decomposition: {120 - or_errors}/120 exact ({or_errors} errors)")

    # 2. Painterly modes (Pollock, Klee, Kandinsky)
    test_uniqueness_and_peeling("pollock", 120, 100)
    test_pollock_extent_peeling(120, 100)
    test_pollock_glaze_homomorphism(120, 100)
    test_pollock_trajectory_homomorphism(120, 100)
    test_klee_uniqueness_and_peeling(120, 100)
    test_uniqueness_and_peeling("kandinsky", 120, 100)
