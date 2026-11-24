"""
Generate publication-quality figures for the Journal of Mathematics and the Arts
manuscript in paper/figures/.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from algebra import factorize, mask_to_grid
from verify_decomposition import (
    hex_to_rgb,
    render_kandinsky_layer,
    render_klee_attenuation,
    render_pollock_layer,
)

FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_tiles():
    data = json.loads((ROOT / "tiles_data.json").read_text())
    return data["width"], data["height"], {int(k): int(v["mask"]) for k, v in data["tiles"].items()}


def format_fac(n: int) -> str:
    if n == 1:
        return "unit"
    facs = factorize(n)
    if len(facs) == 1 and list(facs.values())[0] == 1:
        return "prime"
    parts = [f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(facs.items())]
    return "×".join(parts)


def fig1_xor_grid() -> None:
    w, h, tiles = load_tiles()
    fig, axes = plt.subplots(4, 9, figsize=(11, 5.2))
    fig.patch.set_facecolor("white")

    for idx in range(36):
        n = idx + 1
        ax = axes[idx // 9, idx % 9]
        grid = np.array(mask_to_grid(tiles[n], w, h))
        # Indigo (#1e3a5f) on Cream (#f9f5eb)
        img = np.zeros((h, w, 3), dtype=np.float32)
        fg = np.array([30, 58, 95]) / 255.0
        bg = np.array([249, 245, 235]) / 255.0
        img[grid == 1] = fg
        img[grid == 0] = bg
        ax.imshow(img, interpolation="nearest")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#cccccc")
            spine.set_linewidth(0.7)
        facs = factorize(n)
        is_prime = len(facs) == 1 and list(facs.values())[0] == 1
        title_col = "#166534" if is_prime else "#1e242b"
        ax.set_title(f"{n}", fontsize=9, fontweight="bold", color=title_col, pad=3)
        ax.set_xlabel(format_fac(n), fontsize=6.8, color="#555555", labelpad=2)

    plt.tight_layout(h_pad=0.9, w_pad=0.4)
    fig.savefig(FIG_DIR / "fig1_xor_grid.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


def draw_organic_tile(ax, grid: np.ndarray, fg="#1e3a5f", bg="#f9f5eb") -> None:
    h, w = grid.shape
    ax.set_facecolor(bg)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_aspect("equal")
    for r in range(h):
        for c in range(w):
            if grid[r, c] == 0:
                continue
            circ = patches.Circle((c + 0.5, r + 0.5), 0.39, facecolor=fg, edgecolor="none")
            ax.add_patch(circ)
            if c + 1 < w and grid[r, c + 1] == 1:
                ax.add_patch(patches.Rectangle((c + 0.5, r + 0.22), 1.0, 0.56, facecolor=fg, edgecolor="none"))
            if r + 1 < h and grid[r + 1, c] == 1:
                ax.add_patch(patches.Rectangle((c + 0.22, r + 0.5), 0.56, 1.0, facecolor=fg, edgecolor="none"))
    ax.set_xticks([])
    ax.set_yticks([])


def draw_diamond_tile(ax, grid: np.ndarray, fg="#c85a32", bg="#232528") -> None:
    h, w = grid.shape
    ax.set_facecolor(bg)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_aspect("equal")
    for r in range(h):
        for c in range(w):
            if grid[r, c] == 0:
                continue
            cx, cy = c + 0.5, r + 0.5
            poly = patches.Polygon([[cx, cy - 0.45], [cx + 0.45, cy], [cx, cy + 0.45], [cx - 0.45, cy]],
                                   closed=True, facecolor=fg, edgecolor="none")
            ax.add_patch(poly)
    ax.set_xticks([])
    ax.set_yticks([])


def draw_mandala_tile(ax, grid: np.ndarray, fg="#f0f7ff", bg="#134074") -> None:
    h, w = grid.shape
    ax.set_facecolor(bg)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    max_r = 0.92
    ring_w = max_r / h
    for r in range(h):
        r_in = r * ring_w + 0.01
        r_out = (r + 1) * ring_w - 0.008
        for c in range(w):
            if grid[r, c] == 0:
                continue
            theta1 = 90 - (c + 1) * (360.0 / w) + 2.0
            theta2 = 90 - c * (360.0 / w)
            wedge = patches.Wedge((0, 0), r_out, theta1, theta2, width=(r_out - r_in), facecolor=fg, edgecolor="none")
            ax.add_patch(wedge)
    ax.set_xticks([])
    ax.set_yticks([])


def fig2_xor_presentations() -> None:
    w, h, tiles = load_tiles()
    g30 = np.array(mask_to_grid(tiles[30], w, h))
    g6 = np.array(mask_to_grid(tiles[6], w, h))
    g5 = np.array(mask_to_grid(tiles[5], w, h))

    fig, axes = plt.subplots(2, 4, figsize=(9.5, 4.8))
    fig.patch.set_facecolor("white")

    # Top row: composition Phi(6) * Phi(5) = Phi(30)
    axes[0, 0].imshow(1 - g6, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
    axes[0, 0].set_title(r"$\Phi(6) = \Phi(2 \times 3)$", fontsize=10)
    axes[0, 1].imshow(1 - g5, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
    axes[0, 1].set_title(r"$\Phi(5)$", fontsize=10)
    axes[0, 2].imshow(1 - g30, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
    axes[0, 2].set_title(r"$\Phi(6) \star \Phi(5) = \Phi(30)$", fontsize=10)
    axes[0, 3].axis("off")
    axes[0, 3].text(0.1, 0.5, "Exact 2D cyclic\nXOR-convolution\nover $\\mathbb{F}_2[x,y]/(x^9-1, y^9-1)$\n\nLosslessly invertible\nfrom any 2-tone style",
                    va="center", fontsize=8.5, color="#333333")

    for c in range(3):
        axes[0, c].set_xticks([])
        axes[0, c].set_yticks([])

    # Bottom row: 4 lossless presentations of n=30
    axes[1, 0].imshow(1 - g30, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
    axes[1, 0].set_xticks([]); axes[1, 0].set_yticks([])
    axes[1, 0].set_title("Raw Binary (0/1)", fontsize=9.5)

    draw_organic_tile(axes[1, 1], g30)
    axes[1, 1].set_title("Organic Ink", fontsize=9.5)

    draw_diamond_tile(axes[1, 2], g30)
    axes[1, 2].set_title("Diamond / Woven", fontsize=9.5)

    draw_mandala_tile(axes[1, 3], g30)
    axes[1, 3].set_title("Radial Mandala", fontsize=9.5)

    plt.tight_layout(h_pad=1.2, w_pad=0.8)
    fig.savefig(FIG_DIR / "fig2_xor_presentations.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


def render_composite(mode: str, n: int, size: int = 180) -> np.ndarray:
    facs = factorize(n)
    if mode == "pollock":
        bg = np.array(hex_to_rgb("#f4efe6"), dtype=np.uint8)
        canvas = np.broadcast_to(bg, (size, size, 3)).copy()
        for p in sorted(facs.keys()):
            rgb, mask = render_pollock_layer(p, 1, size=size, steps=32 * facs[p])
            canvas[mask] = rgb[mask]
        return canvas
    if mode == "klee":
        bg = np.array(hex_to_rgb("#f6f0e2"), dtype=np.float32)
        canvas = np.broadcast_to(bg, (size, size, 3)).copy()
        for p, e in sorted(facs.items()):
            canvas *= render_klee_attenuation(p, e, size=size)
        return np.clip(np.round(canvas), 0, 255).astype(np.uint8)
    # kandinsky
    bg = np.array(hex_to_rgb("#f4ede0"), dtype=np.uint8)
    canvas = np.broadcast_to(bg, (size, size, 3)).copy()
    for p in sorted(facs.keys()):
        for k in range(1, facs[p] + 1):
            rgb, mask = render_kandinsky_layer(p, k, size=size)
            canvas[mask] = rgb[mask]
    return canvas


def fig3_painterly_gallery() -> None:
    rows_nums = [
        [2, 4, 8, 6, 12, 30],
        [32, 36, 60, 96, 105, 120],
    ]
    modes = [
        ("pollock", "Pollock\nDrip-Paths"),
        ("klee", "Klee 1914\nWatercolor"),
        ("kandinsky", "Kandinsky\nComp. VIII"),
    ]
    fig, axes = plt.subplots(len(modes) * 2, 6, figsize=(10.5, 10.6))
    fig.patch.set_facecolor("white")

    for m_idx, (mode, label) in enumerate(modes):
        for sub_r, nums in enumerate(rows_nums):
            r = m_idx * 2 + sub_r
            for c, n in enumerate(nums):
                ax = axes[r, c]
                img = render_composite(mode, n, size=180)
                ax.imshow(img)
                ax.set_xticks([])
                ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_edgecolor("#bbbbbb")
                    spine.set_linewidth(0.7)
                ax.set_title(f"$n={n}$ ({format_fac(n)})", fontsize=8.2, fontweight="bold", pad=3)
                if c == 0 and sub_r == 0:
                    ax.set_ylabel(label, fontsize=9, fontweight="bold", rotation=0, labelpad=44, va="top")

    plt.tight_layout(h_pad=0.75, w_pad=0.45)
    fig.savefig(FIG_DIR / "fig3_painterly_gallery.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


def fig4_peeling_decomposition() -> None:
    w, h, tiles = load_tiles()
    size = 180
    nums = [30, 6, 2, 1]

    fig, axes = plt.subplots(4, 4, figsize=(9.6, 8.2))
    fig.patch.set_facecolor("white")

    # Row 1: Binary XOR-Convolution (9x9)
    xor_titles = [
        "Input $M(30)$\n($2 \\times 3 \\times 5$)",
        "Unmix $p=5$\nResidual $M(6)$",
        "Unmix $p=3$\nResidual $M(2)$",
        "Unmix $p=2$\nIdentity $M(1)$",
    ]
    fg = np.array([30, 58, 95]) / 255.0
    bg_xor = np.array([249, 245, 235]) / 255.0
    for c, (n, title) in enumerate(zip(nums, xor_titles)):
        ax = axes[0, c]
        grid = np.array(mask_to_grid(tiles[n], w, h))
        img = np.zeros((h, w, 3), dtype=np.float32)
        img[grid == 1] = fg
        img[grid == 0] = bg_xor
        ax.imshow(img, interpolation="nearest")
        ax.set_title(title, fontsize=8.5)
        ax.set_xticks([]); ax.set_yticks([])
        if c == 0:
            ax.set_ylabel("Binary\nXOR-Conv.", fontsize=8.8, fontweight="bold", rotation=0, labelpad=42, va="center")

    # Rows 2-4: Pollock, Klee, Kandinsky
    painterly_rows = [
        ("pollock", "Pollock\nDrip-Paths", [
            "Input $I(30)$", "Peel $p=5$\nResidual $I(6)$", "Peel $p=3$\nResidual $I(2)$", "Peel $p=2$\nIdentity $I(1)$"
        ]),
        ("klee", "Klee 1914\nWatercolor", [
            "Input $I(30)$", "Divide $A_{5,1}$\nResidual $I(6)$", "Divide $A_{3,1}$\nResidual $I(2)$", "Divide $A_{2,1}$\nIdentity $I(1)$"
        ]),
        ("kandinsky", "Kandinsky\nComp. VIII", [
            "Input $I(30)$", "Peel $p=5$\nResidual $I(6)$", "Peel $p=3$\nResidual $I(2)$", "Peel $p=2$\nIdentity $I(1)$"
        ]),
    ]

    for r_off, (mode, label, titles) in enumerate(painterly_rows, start=1):
        for c, (n, title) in enumerate(zip(nums, titles)):
            ax = axes[r_off, c]
            img = render_composite(mode, n, size=size)
            ax.imshow(img)
            ax.set_title(title, fontsize=8.5)
            ax.set_xticks([]); ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor("#bbbbbb")
                spine.set_linewidth(0.7)
            if c == 0:
                ax.set_ylabel(label, fontsize=8.8, fontweight="bold", rotation=0, labelpad=42, va="center")

    plt.tight_layout(h_pad=0.9, w_pad=0.6)
    fig.savefig(FIG_DIR / "fig4_peeling_decomposition.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


def fig5_message_matharts() -> None:
    w, h, tiles = load_tiles()
    word = "MathArts"
    chars = list(word)
    codes = [ord(ch) for ch in chars]

    fig, axes = plt.subplots(4, len(chars), figsize=(11.2, 5.8))
    fig.patch.set_facecolor("white")

    # Row 0: Binary XOR-Convolution rendered in Organic Ink (lossless)
    for c, (ch, n) in enumerate(zip(chars, codes)):
        ax = axes[0, c]
        grid = np.array(mask_to_grid(tiles[n], w, h))
        draw_organic_tile(ax, grid)
        for spine in ax.spines.values():
            spine.set_edgecolor("#bbbbbb")
            spine.set_linewidth(0.7)
        ax.set_title(f"'{ch}' ({n})\n[{format_fac(n)}]", fontsize=8.2, fontweight="bold", pad=3)
        if c == 0:
            ax.set_ylabel("XOR-Conv.\n(Organic Ink)", fontsize=8.5, fontweight="bold", rotation=0, labelpad=44, va="center")

    # Rows 1-3: Pollock, Klee 1914 Watercolor, Kandinsky Comp. VIII
    painterly = [
        ("pollock", "Pollock\nDrip-Paths"),
        ("klee", "Klee 1914\nWatercolor"),
        ("kandinsky", "Kandinsky\nComp. VIII"),
    ]
    for r_idx, (mode, label) in enumerate(painterly, start=1):
        for c, n in enumerate(codes):
            ax = axes[r_idx, c]
            img = render_composite(mode, n, size=180)
            ax.imshow(img)
            ax.set_xticks([]); ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor("#bbbbbb")
                spine.set_linewidth(0.7)
            if c == 0:
                ax.set_ylabel(label, fontsize=8.5, fontweight="bold", rotation=0, labelpad=44, va="center")

    plt.tight_layout(h_pad=0.6, w_pad=0.4)
    fig.savefig(FIG_DIR / "fig5_message_matharts.pdf", bbox_inches="tight", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    fig1_xor_grid()
    fig2_xor_presentations()
    fig3_painterly_gallery()
    fig4_peeling_decomposition()
    fig5_message_matharts()
    print("Generated all figures in", FIG_DIR)
