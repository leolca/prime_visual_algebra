"""
Single-Canvas Pollock Visual Codec with Rotation, Translation, and Scale (RTS) Resilience.

Encodes an arbitrary byte message (e.g., "Leonardo", 64 bits) onto ONE 512x512
Pollock canvas by mapping bit i -> prime p_i using translucent multiply glazing,
with 3 disguised asymmetric paint-pool fiducials for RTS alignment.
"""

from __future__ import annotations
import io
import math
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image, ImageDraw

from algebra import primes_up_to
from verify_decomposition import hex_to_rgb, hsl_to_rgb, mulberry32

# Reserve hues in [20, 330] for primes; reserve pure crimson (#a80818) for the 3 anchor pools
ANCHOR_HEX = "#a80818"
ANCHOR_RGB = np.array(hex_to_rgb(ANCHOR_HEX), dtype=np.float32)
BG_HEX = "#f4efe6"
BG_RGB = np.array(hex_to_rgb(BG_HEX), dtype=np.float32)


def get_first_k_primes(k: int) -> List[int]:
    n = 100
    while True:
        ps = primes_up_to(n)
        if len(ps) >= k:
            return ps[:k]
        n *= 2


def prime_color_pollock(idx: int) -> Tuple[int, int, int]:
    # Keep hue away from 345..15 deg (reserved for crimson anchor pools)
    hue = 25.0 + ((idx * 137.508) % 305.0)
    sat = 68.0 + ((idx * 13) % 18)
    light = 42.0
    return hsl_to_rgb(hue, sat, light)


def render_prime_stroke_mask(p: int, idx: int, size: int = 512, steps: int = 28) -> Tuple[np.ndarray, np.ndarray]:
    """Return (rgb_u8, boolean_mask) for prime p's single Pollock drip trajectory."""
    seed = ((p * 2654435761) ^ 0x40503311) & 0xFFFFFFFF
    rand = mulberry32(seed)
    color = prime_color_pollock(idx)

    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    margin = size * 0.12
    span = size - 2 * margin
    x = margin + rand() * span
    y = margin + rand() * span
    angle = rand() * math.pi * 2
    speed = size * (0.06 + rand() * 0.11)

    for _ in range(steps):
        angle += (rand() - 0.5) * 1.9
        speed = max(size * 0.025, min(size * 0.18, speed * (0.75 + rand() * 0.55)))
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
        lw = max(2, int(round((1.15 - speed / (size * 0.18)) * size * 0.022)))
        draw.line([(x, y), (cx, cy), (nx, ny)], fill=255, width=lw)
        if rand() < 0.35:
            rr = lw * (0.6 + rand() * 0.9)
            ox = nx + (rand() - 0.5) * lw * 1.6
            oy = ny + (rand() - 0.5) * lw * 1.6
            draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=255)
        x, y = nx, ny

    mask = np.array(img) > 0
    rgb = np.array(color, dtype=np.uint8)
    return rgb, mask


def canonical_anchors(size: int) -> List[Tuple[float, float, float]]:
    """Three asymmetric anchor paint pools: (x, y, radius) sorted largest to smallest."""
    return [
        (size * 0.07, size * 0.07, size * 0.024),
        (size * 0.93, size * 0.07, size * 0.017),
        (size * 0.07, size * 0.93, size * 0.011),
    ]


def encode_message_pollock(message: str, size: int = 512, alpha: float = 0.55) -> Tuple[Image.Image, List[int]]:
    """Encode an ASCII/UTF-8 string onto a single Pollock canvas using multiply glazing."""
    raw = message.encode("utf-8")
    bits: List[int] = []
    for byte in raw:
        for b in range(7, -1, -1):
            bits.append((byte >> b) & 1)

    primes = get_first_k_primes(len(bits))
    canvas = np.broadcast_to(BG_RGB, (size, size, 3)).copy()

    for idx, (bit, p) in enumerate(zip(bits, primes)):
        if bit == 1:
            rgb, mask = render_prime_stroke_mask(p, idx, size=size)
            col = rgb.astype(np.float32) / 255.0
            canvas[mask] *= (1.0 - alpha) + alpha * col

    img = Image.fromarray(np.clip(np.round(canvas), 0, 255).astype(np.uint8))
    # Paint the 3 disguised anchor paint pools on top so they remain clearly detectable
    draw = ImageDraw.Draw(img)
    ac = tuple(int(v) for v in ANCHOR_RGB)
    for ax, ay, ar in canonical_anchors(size):
        draw.ellipse([ax - ar, ay - ar, ax + ar, ay + ar], fill=ac)
    return img, bits


def apply_rts_distortion(
    img: Image.Image,
    angle_deg: float = 0.0,
    scale: float = 1.0,
    shift: Tuple[float, float] = (0.0, 0.0),
    noise_std: float = 0.0,
    jpeg_quality: int | None = None,
    seed: int = 0,
) -> Image.Image:
    """Apply Rotation, Translation, Scaling, optional Gaussian noise, and JPEG compression."""
    w, h = img.size
    bg_tuple = tuple(int(v) for v in BG_RGB)
    # Create a slightly larger padded canvas so rotated/scaled corners don't clip
    pad = int(w * 0.25)
    big = Image.new("RGB", (w + 2 * pad, h + 2 * pad), bg_tuple)
    big.paste(img, (pad, pad))

    # Scale around center, rotate, then translate
    new_w, new_h = int(round(big.width * scale)), int(round(big.height * scale))
    scaled = big.resize((new_w, new_h), Image.Resampling.BILINEAR)
    rotated = scaled.rotate(angle_deg, resample=Image.Resampling.BILINEAR, fillcolor=bg_tuple)

    # Crop back to (w + 2*pad) centered + shift
    cx, cy = rotated.width / 2 - shift[0], rotated.height / 2 - shift[1]
    left = int(round(cx - (w + 2 * pad) / 2))
    top = int(round(cy - (h + 2 * pad) / 2))
    out = rotated.crop((left, top, left + w + 2 * pad, top + h + 2 * pad))

    if noise_std > 0:
        rng = np.random.default_rng(seed)
        arr = np.array(out, dtype=np.float32) + rng.normal(0.0, noise_std, size=(out.height, out.width, 3))
        out = Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8))

    if jpeg_quality is not None:
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=jpeg_quality)
        buf.seek(0)
        out = Image.open(buf).convert("RGB")

    return out


def detect_three_anchors(arr: np.ndarray) -> List[Tuple[float, float]]:
    """Detect the 3 largest crimson anchor blobs and return centroids sorted by area descending."""
    # Red-dominant score: high R, low G and B
    r, g, b = arr[:, :, 0].astype(np.float32), arr[:, :, 1].astype(np.float32), arr[:, :, 2].astype(np.float32)
    dist = np.sqrt((r - ANCHOR_RGB[0]) ** 2 + (g - ANCHOR_RGB[1]) ** 2 + (b - ANCHOR_RGB[2]) ** 2)
    mask = dist < 55.0

    # Simple 4-connected component labeling via BFS
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    comps: List[Tuple[int, float, float]] = []
    ys, xs = np.where(mask)
    for sy, sx in zip(ys, xs):
        if visited[sy, sx]:
            continue
        stack = [(int(sy), int(sx))]
        visited[sy, sx] = True
        pts = []
        while stack:
            cy, cx = stack.pop()
            pts.append((cx, cy))
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    stack.append((ny, nx))
        if len(pts) >= 12:
            mx = sum(p[0] for p in pts) / len(pts)
            my = sum(p[1] for p in pts) / len(pts)
            comps.append((len(pts), mx, my))

    comps.sort(key=lambda c: c[0], reverse=True)
    if len(comps) < 3:
        raise RuntimeError(f"Expected 3 anchor blobs, found {len(comps)}")
    return [(c[1], c[2]) for c in comps[:3]]


def align_image_rts(distorted: Image.Image, target_size: int = 512) -> Image.Image:
    """Recover similarity transform from 3 anchor centroids and warp back to canonical frame."""
    arr = np.array(distorted)
    src_pts = detect_three_anchors(arr)  # [(x, y), ...] sorted largest to smallest
    dst_pts = [(ax, ay) for ax, ay, _ in canonical_anchors(target_size)]

    # Solve for affine/similarity matrix mapping dst (output) -> src (input) for PIL.Image.transform
    # src_x = a * dst_x + b * dst_y + c
    # src_y = d * dst_x + e * dst_y + f
    A = np.array([[x, y, 1.0] for x, y in dst_pts], dtype=np.float64)
    bx = np.array([x for x, _ in src_pts], dtype=np.float64)
    by = np.array([y for _, y in src_pts], dtype=np.float64)
    px = np.linalg.solve(A, bx)
    py = np.linalg.solve(A, by)
    coeffs = (px[0], px[1], px[2], py[0], py[1], py[2])
    return distorted.transform((target_size, target_size), Image.Transform.AFFINE, coeffs, resample=Image.Resampling.BILINEAR)


def decode_message_pollock(img: Image.Image, n_bits: int, size: int = 512, alpha: float = 0.55) -> Tuple[str, List[int]]:
    """Decode n_bits from an aligned Pollock canvas using soft matched-filter scoring."""
    aligned = align_image_rts(img, target_size=size)
    arr = np.array(aligned, dtype=np.float32)
    residual = np.clip(arr / BG_RGB, 0.0, 1.0)

    primes = get_first_k_primes(n_bits)
    rec_bits: List[int] = []
    for idx, p in enumerate(primes):
        rgb, mask = render_prime_stroke_mask(p, idx, size=size)
        col = rgb.astype(np.float32) / 255.0
        expected_att = (1.0 - alpha) + alpha * col  # 3-vector in (0, 1]

        # For a pixel where prime p is painted (even if overlapped by other primes),
        # residual <= expected_att (with slight tolerance for bilinear resampling/noise).
        # Specifically, compute fraction of mask pixels matching residual <= expected_att + tol
        # AND having significant darkening (distance from white paper).
        pix_res = residual[mask]
        # Soft check: how many pixels in this prime's footprint are at least 85% as dark as expected_att?
        match_frac = float(np.mean(np.all(pix_res <= expected_att + 0.08, axis=1)))
        rec_bits.append(1 if match_frac >= 0.72 else 0)

    # Convert bits back to UTF-8 bytes
    out_bytes = bytearray()
    for i in range(0, len(rec_bits), 8):
        val = 0
        for b in range(8):
            val = (val << 1) | rec_bits[i + b]
        out_bytes.append(val)
    return out_bytes.decode("utf-8", errors="replace"), rec_bits


if __name__ == "__main__":
    msg = "Leonardo"
    canvas_img, true_bits = encode_message_pollock(msg, size=512, alpha=0.55)
    print(f"Encoded '{msg}' ({len(true_bits)} bits, primes 2..{get_first_k_primes(len(true_bits))[-1]}) on 1 canvas (512x512).")

    scenarios = [
        ("Clean canonical", dict(angle_deg=0.0, scale=1.0, shift=(0, 0), noise_std=0.0, jpeg_quality=None)),
        ("Rotated 27 deg, 0.85x, shifted", dict(angle_deg=27.0, scale=0.85, shift=(18, -14), noise_std=0.0, jpeg_quality=None)),
        ("Rotated 143 deg, 1.15x, JPEG q=80", dict(angle_deg=143.0, scale=1.15, shift=(-22, 15), noise_std=0.0, jpeg_quality=80)),
        ("Rotated -38 deg, Gaussian noise std=8", dict(angle_deg=-38.0, scale=0.95, shift=(10, 12), noise_std=8.0, jpeg_quality=None)),
    ]

    for label, kw in scenarios:
        distorted = apply_rts_distortion(canvas_img, **kw)
        rec_msg, rec_bits = decode_message_pollock(distorted, len(true_bits), size=512, alpha=0.55)
        bit_acc = sum(t == r for t, r in zip(true_bits, rec_bits))
        print(f"  [{label}] -> '{rec_msg}' | bits: {bit_acc}/{len(true_bits)}")
