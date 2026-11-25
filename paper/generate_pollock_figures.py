"""
Generate publication-quality figures for the focused Pollock Visual Algebra paper.
"""

from __future__ import annotations
import math
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from algebra import factorize, primes_up_to
from pollock_codec import align_image_organic, apply_rts_distortion, encode_message_pollock
from verify_decomposition import hex_to_rgb, hsl_to_rgb, mulberry32, render_pollock_layer

FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

PRIMES = primes_up_to(120)
PRIME_INDEX = {p: idx for idx, p in enumerate(PRIMES)}
BG = np.array(hex_to_rgb("#f4efe6"), dtype=np.uint8)
BG_F = BG.astype(np.float32)


def format_fac(n: int) -> str:
    if n == 1:
        return "unit"
    facs = factorize(n)
    if len(facs) == 1 and list(facs.values())[0] == 1:
        return "prime"
    return "×".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(facs.items()))


def render_pollock_variant(variant: str, n: int, size: int = 180) -> np.ndarray:
    facs = factorize(n)
    if variant == "separate":
        canvas = np.broadcast_to(BG, (size, size, 3)).copy()
        for p in sorted(facs.keys()):
            for k in range(1, facs[p] + 1):
                rgb, mask = render_pollock_layer(p, k, size=size, steps=32)
                canvas[mask] = rgb[mask]
        return canvas
    if variant == "extent":
        canvas = np.broadcast_to(BG, (size, size, 3)).copy()
        for p in sorted(facs.keys()):
            rgb, mask = render_pollock_layer(p, 1, size=size, steps=32 * facs[p])
            canvas[mask] = rgb[mask]
        return canvas
    if variant == "glaze":
        alpha = 0.45 * 0.88
        att = np.ones((size, size, 3), dtype=np.float32)
        for p, e in sorted(facs.items()):
            rgb, mask = render_pollock_layer(p, 1, size=size, steps=32)
            col = rgb.astype(np.float32) / 255.0
            a_p = np.ones((size, size, 3), dtype=np.float32)
            a_p[mask] = (1.0 - alpha) + alpha * col[mask]
            att *= (a_p ** e)
        return np.clip(np.round(BG_F * att), 0, 255).astype(np.uint8)

    # trajectory
    num_pts = 80
    ts = np.linspace(0.0, 1.0, num_pts + 1)
    gamma = np.zeros((num_pts + 1, 2), dtype=np.float64)
    for p, e in facs.items():
        seed = ((p * 2654435761) ^ 0x7F4A7C15) & 0xFFFFFFFF
        rand = mulberry32(seed)
        for m in range(1, 7):
            amp = 0.13 / math.sqrt(m)
            fx, fy = 1 + int(rand() * 7), 1 + int(rand() * 7)
            px, py = rand() * math.pi * 2, rand() * math.pi * 2
            ax, ay = amp * (0.6 + 0.8 * rand()), amp * (0.6 + 0.8 * rand())
            gamma[:, 0] += e * ax * np.cos(2 * math.pi * fx * ts + px)
            gamma[:, 1] += e * ay * np.sin(2 * math.pi * fy * ts + py)

    img = Image.new("RGB", (size, size), tuple(int(v) for v in BG))
    draw = ImageDraw.Draw(img)
    if facs:
        sx = sum(e * math.cos(math.radians((PRIME_INDEX[p] * 137.508 + 18) % 360)) for p, e in facs.items())
        sy = sum(e * math.sin(math.radians((PRIME_INDEX[p] * 137.508 + 18) % 360)) for p, e in facs.items())
        hue = (math.degrees(math.atan2(sy, sx)) + 360) % 360
        col = hsl_to_rgb(hue, 74.0, 40.0)
        margin = size * 0.06
        span = size - 2 * margin
        pts = [(margin + (((0.5 + x) % 1.0) * span), margin + (((0.5 + y) % 1.0) * span)) for x, y in gamma]
        for i in range(len(pts) - 1):
            if math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) <= span * 0.45:
                draw.line([pts[i], pts[i + 1]], fill=col, width=max(2, size // 64))
    return np.array(img)


def fig1_pollock_modes() -> None:
    nums = [2, 4, 8, 6, 12, 30]
    variants = [
        ("separate", "Separate Strokes\n(Grammar)"),
        ("extent", "Path Extent\n(Grammar)"),
        ("glaze", "Translucent Multiply\n(Pixel-Space Hom.)"),
        ("trajectory", "Trajectory Sum\n(Traj.-Space Hom.)"),
    ]
    fig, axes = plt.subplots(len(variants), len(nums), figsize=(10.5, 7.2))
    fig.patch.set_facecolor("white")
    for r, (v, label) in enumerate(variants):
        for c, n in enumerate(nums):
            ax = axes[r, c]
            ax.imshow(render_pollock_variant(v, n, size=180))
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_edgecolor("#bbbbbb"); sp.set_linewidth(0.7)
            if r == 0:
                ax.set_title(f"$n={n}$\n({format_fac(n)})", fontsize=9, fontweight="bold")
            if c == 0:
                ax.set_ylabel(label, fontsize=8.5, fontweight="bold", rotation=0, labelpad=48, va="center")
    plt.tight_layout(h_pad=0.6, w_pad=0.5)
    fig.savefig(FIG_DIR / "fig1_pollock_modes.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


def fig2_pollock_homomorphism() -> None:
    fig, axes = plt.subplots(2, 3, figsize=(7.5, 4.8))
    fig.patch.set_facecolor("white")
    pairs = [
        ("glaze", "Translucent Multiply Glazing:\n$I(6) \\star I(10) = I(60)$"),
        ("trajectory", "Toroidal Trajectory Sum:\n$\\gamma(6) + \\gamma(10) \\equiv \\gamma(60)$"),
    ]
    nums = [6, 10, 60]
    for r, (v, label) in enumerate(pairs):
        for c, n in enumerate(nums):
            ax = axes[r, c]
            ax.imshow(render_pollock_variant(v, n, size=200))
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_edgecolor("#bbbbbb"); sp.set_linewidth(0.7)
            sym = "=" if c == 2 else ("$\\star$" if c == 0 else "")
            ax.set_title(f"$n={n}$ ({format_fac(n)})", fontsize=9, fontweight="bold")
            if c == 0:
                ax.set_ylabel(label, fontsize=8.5, fontweight="bold", rotation=0, labelpad=58, va="center")
    plt.tight_layout(h_pad=0.8, w_pad=0.8)
    fig.savefig(FIG_DIR / "fig2_pollock_homomorphism.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


def fig3_pollock_peeling() -> None:
    nums = [30, 6, 2, 1]
    titles = [
        "Input $I(30)$\n($2 \\times 3 \\times 5$)",
        "Divide $A_5$\nResidual $I(6)$",
        "Divide $A_3$\nResidual $I(2)$",
        "Divide $A_2$\nIdentity $I(1)$",
    ]
    fig, axes = plt.subplots(1, 4, figsize=(9.2, 2.5))
    fig.patch.set_facecolor("white")
    for ax, n, t in zip(axes, nums, titles):
        ax.imshow(render_pollock_variant("glaze", n, size=200))
        ax.set_title(t, fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor("#bbbbbb"); sp.set_linewidth(0.7)
    plt.tight_layout(w_pad=0.8)
    fig.savefig(FIG_DIR / "fig3_pollock_peeling.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


def fig4_pollock_matharts_rts() -> None:
    img, _ = encode_message_pollock("MathArts", size=512, alpha=0.50)
    d1 = apply_rts_distortion(img, angle_deg=143.0, scale=1.15, shift=(-22, 15), jpeg_quality=80)
    a1 = align_image_organic(d1, target_size=512)
    d2 = apply_rts_distortion(img, angle_deg=-38.0, scale=0.95, shift=(10, 12), noise_std=8.0, seed=1)

    panels = [
        (img, "(a) Canonical 64-bit Canvas\n(\"MathArts\", primes 2..311)"),
        (d1, "(b) Rotated $143^\\circ$, $1.15\\times$,\nShifted, JPEG $q=80$"),
        (a1, "(c) Fourier--Mellin Aligned (b)\nDecoded: \"MathArts\" (64/64 bits)"),
        (d2, "(d) Rotated $-38^\\circ$, Noise $\\sigma=8$\nDecoded: \"MathArts\" (64/64 bits)"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(11.0, 3.0))
    fig.patch.set_facecolor("white")
    for ax, (im, title) in zip(axes, panels):
        ax.imshow(np.array(im))
        ax.set_title(title, fontsize=8.3)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor("#bbbbbb"); sp.set_linewidth(0.7)
    plt.tight_layout(w_pad=0.6)
    fig.savefig(FIG_DIR / "fig4_pollock_matharts_rts.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    fig1_pollock_modes()
    fig2_pollock_homomorphism()
    fig3_pollock_peeling()
    fig4_pollock_matharts_rts()
    print("Generated Pollock paper figures in", FIG_DIR)
