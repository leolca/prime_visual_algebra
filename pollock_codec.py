"""
Single-Canvas Pollock Visual Codec with Integrated Organic Underpainting Alignment
(No external fiducial dots — uses an organic Pollock base pour + Fourier-Mellin RTS alignment).
"""

from __future__ import annotations
import io
import math
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageDraw

from algebra import primes_up_to
from verify_decomposition import hex_to_rgb, hsl_to_rgb, mulberry32

# Foundational organic Pollock top-skein color (deep Venetian crimson, integrated into the painting)
BASE_POUR_HEX = "#8b101c"
BASE_POUR_RGB = np.array(hex_to_rgb(BASE_POUR_HEX), dtype=np.float32)
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
    # Keep hue away from 340..20 deg (reserved for the foundational Venetian umber-crimson pour)
    hue = 28.0 + ((idx * 137.508) % 302.0)
    sat = 66.0 + ((idx * 13) % 18)
    light = 43.0
    return hsl_to_rgb(hue, sat, light)


def render_stroke_mask(seed: int, size: int = 512, steps: int = 28, margin_frac: float = 0.10, lw_scale: float = 0.022) -> np.ndarray:
    """Return boolean mask of an organic Pollock drip trajectory."""
    rand = mulberry32(seed & 0xFFFFFFFF)
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    margin = size * margin_frac
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
        lw = max(2, int(round((1.15 - speed / (size * 0.18)) * size * lw_scale)))
        draw.line([(x, y), (cx, cy), (nx, ny)], fill=255, width=lw)
        if rand() < 0.35:
            rr = lw * (0.6 + rand() * 0.9)
            ox = nx + (rand() - 0.5) * lw * 1.6
            oy = ny + (rand() - 0.5) * lw * 1.6
            draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=255)
        x, y = nx, ny

    return np.array(img) > 0


def render_prime_stroke_mask(p: int, idx: int, size: int = 512, steps: int = 28) -> Tuple[np.ndarray, np.ndarray]:
    seed = ((p * 2654435761) ^ 0x40503311) & 0xFFFFFFFF
    mask = render_stroke_mask(seed, size=size, steps=steps, margin_frac=0.10, lw_scale=0.022)
    rgb = np.array(prime_color_pollock(idx), dtype=np.uint8)
    return rgb, mask


def render_base_pour_mask(size: int = 512) -> np.ndarray:
    """Organic foundational Pollock pour used for both aesthetics and RTS registration."""
    return render_stroke_mask(seed=0x20261124, size=size, steps=26, margin_frac=0.12, lw_scale=0.028)


def encode_bits_pollock(bits: List[int], size: int = 512, alpha: float = 0.50) -> Image.Image:
    """Encode an arbitrary bit list onto a single Pollock canvas with an opaque organic top-skein."""
    primes = get_first_k_primes(len(bits))
    canvas = np.broadcast_to(BG_RGB, (size, size, 3)).copy()

    for idx, (bit, p) in enumerate(zip(bits, primes)):
        if bit == 1:
            rgb, mask = render_prime_stroke_mask(p, idx, size=size)
            col = rgb.astype(np.float32) / 255.0
            canvas[mask] *= (1.0 - alpha) + alpha * col

    # Paint the organic Pollock top-skein (uniform pigment for clean Fourier-Mellin registration)
    base_mask = render_base_pour_mask(size=size)
    canvas[base_mask] = BASE_POUR_RGB
    return Image.fromarray(np.clip(np.round(canvas), 0, 255).astype(np.uint8))


def encode_message_pollock(message: str, size: int = 512, alpha: float = 0.50) -> Tuple[Image.Image, List[int]]:
    """Encode an ASCII/UTF-8 string onto a single Pollock canvas with an organic top-skein."""
    raw = message.encode("utf-8")
    bits: List[int] = []
    for byte in raw:
        for b in range(7, -1, -1):
            bits.append((byte >> b) & 1)
    return encode_bits_pollock(bits, size=size, alpha=alpha), bits


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
    pad = int(w * 0.25)
    big = Image.new("RGB", (w + 2 * pad, h + 2 * pad), bg_tuple)
    big.paste(img, (pad, pad))

    new_w, new_h = int(round(big.width * scale)), int(round(big.height * scale))
    scaled = big.resize((new_w, new_h), Image.Resampling.BILINEAR)
    rotated = scaled.rotate(angle_deg, resample=Image.Resampling.BILINEAR, fillcolor=bg_tuple)

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


def extract_base_pour_score(arr: np.ndarray) -> np.ndarray:
    """Extract soft response map for the opaque Venetian crimson top-skein."""
    diff = arr.astype(np.float32) - BASE_POUR_RGB
    dist = np.sqrt(np.sum(diff ** 2, axis=2))
    return np.exp(-(dist / 30.0) ** 2).astype(np.float32)


def logpolar_fft_register(ref: np.ndarray, mov: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Recover (angle_deg, scale, dx, dy) mapping ref -> mov using Fourier-Mellin (log-polar FFT)
    followed by coarse-to-fine local refinement.
    """
    H, W = mov.shape
    # Pad ref to (H, W) centered
    rh, rw = ref.shape
    ref_pad = np.zeros((H, W), dtype=np.float32)
    y0, x0 = (H - rh) // 2, (W - rw) // 2
    ref_pad[y0:y0 + rh, x0:x0 + rw] = ref

    # 1. FFT magnitude spectra (translation invariant!)
    f_ref = np.abs(np.fft.fftshift(np.fft.fft2(ref_pad)))
    f_mov = np.abs(np.fft.fftshift(np.fft.fft2(mov)))

    # Suppress DC & apply high-pass emphasis
    cy, cx = H // 2, W // 2
    yy, xx = np.ogrid[:H, :W]
    rad = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    hp = np.clip(rad / 8.0, 0.0, 1.0)
    f_ref *= hp
    f_mov *= hp

    # 2. Resample magnitudes onto log-polar grid (N_ang x N_rad)
    N_ang, N_rad = 180, 96
    r_min, r_max = 3.0, min(H, W) * 0.45
    thetas = np.linspace(0.0, math.pi, N_ang, endpoint=False)  # 180-deg symmetry of real FFT mag
    log_rs = np.linspace(math.log(r_min), math.log(r_max), N_rad)
    rs = np.exp(log_rs)
    grid_y = cy + np.outer(np.sin(thetas), rs)
    grid_x = cx + np.outer(np.cos(thetas), rs)

    def sample_bilinear(img_arr: np.ndarray, gy: np.ndarray, gx: np.ndarray) -> np.ndarray:
        y0i = np.clip(np.floor(gy).astype(int), 0, H - 2)
        x0i = np.clip(np.floor(gx).astype(int), 0, W - 2)
        wy = gy - y0i
        wx = gx - x0i
        return (
            img_arr[y0i, x0i] * (1 - wy) * (1 - wx)
            + img_arr[y0i, x0i + 1] * (1 - wy) * wx
            + img_arr[y0i + 1, x0i] * wy * (1 - wx)
            + img_arr[y0i + 1, x0i + 1] * wy * wx
        )

    lp_ref = sample_bilinear(f_ref, grid_y, grid_x)
    lp_mov = sample_bilinear(f_mov, grid_y, grid_x)

    # 3. Phase correlation in log-polar space gives (d_theta, d_log_r)
    F1 = np.fft.fft2(lp_ref)
    F2 = np.fft.fft2(lp_mov)
    R = F1 * np.conj(F2)
    R /= np.maximum(np.abs(R), 1e-8)
    corr_lp = np.real(np.fft.ifft2(R))

    # Restrict scale search to reasonable [0.65, 1.5]
    max_shift_r = int(round(math.log(1.55) / (log_rs[1] - log_rs[0])))
    best_val = -1.0
    best_ia, best_ir = 0, 0
    for ir in list(range(0, max_shift_r + 1)) + list(range(N_rad - max_shift_r, N_rad)):
        col = corr_lp[:, ir]
        ia = int(np.argmax(col))
        if col[ia] > best_val:
            best_val = float(col[ia])
            best_ia, best_ir = ia, ir

    # Convert index shifts to angle & scale (note 180-deg ambiguity resolved below)
    # In image coords (y downward), CCW rotation by +ang shifts theta by -ang;
    # phase correlation R = F1 * conj(F2) gives shift = ref_idx - mov_idx.
    shift_ia = best_ia if best_ia <= N_ang // 2 else best_ia - N_ang
    shift_ir = best_ir if best_ir <= N_rad // 2 else best_ir - N_rad
    d_ang = shift_ia * (180.0 / N_ang)
    d_lr = shift_ir * (log_rs[1] - log_rs[0])
    est_scale = math.exp(-d_lr)

    # 4. Test both d_ang and d_ang + 180 (and +/- signs) via Cartesian FFT cross-correlation
    ref_img = Image.fromarray((ref * 255).astype(np.uint8))
    best_score = -1.0
    best_params = (0.0, 1.0, 0.0, 0.0)
    F_mov = np.fft.fft2(mov)

    def eval_candidate(ang: float, sc: float) -> Tuple[float, float, float]:
        nw, nh = max(8, int(round(rw * sc))), max(8, int(round(rh * sc)))
        r_sc = ref_img.resize((nw, nh), Image.Resampling.BILINEAR)
        r_rot = r_sc.rotate(ang, expand=True, resample=Image.Resampling.BILINEAR)
        tpl = np.zeros((H, W), dtype=np.float32)
        r_arr = np.array(r_rot, dtype=np.float32) / 255.0
        # Center-crop if r_rot exceeds (H, W) so its center stays exact
        sy0 = max(0, (r_rot.height - H) // 2)
        sx0 = max(0, (r_rot.width - W) // 2)
        th = min(H, r_rot.height)
        tw = min(W, r_rot.width)
        r_crop = r_arr[sy0:sy0 + th, sx0:sx0 + tw]
        tpl[:th, :tw] = r_crop
        norm_tpl = float(np.sqrt(np.sum(r_crop ** 2))) + 1e-6
        cc = np.real(np.fft.ifft2(F_mov * np.conj(np.fft.fft2(tpl))))
        iy, ix = np.unravel_index(np.argmax(cc), cc.shape)
        dy = float(iy if iy <= H // 2 else iy - H)
        dx = float(ix if ix <= W // 2 else ix - W)
        # Normalized cross-correlation score avoids bias toward larger scales
        return float(cc[iy, ix]) / norm_tpl, dx + (tw - W) / 2.0, dy + (th - H) / 2.0

    cand_angles = {d_ang, d_ang + 180.0, -d_ang, -d_ang + 180.0}
    cand_scales = {est_scale, 1.0 / max(est_scale, 0.1)}
    for base_ang in cand_angles:
        for base_sc in cand_scales:
            if not (0.55 <= base_sc <= 1.75):
                continue
            for da in (-2.0, 0.0, 2.0):
                for ds in (0.97, 1.0, 1.03):
                    sc_val, dx, dy = eval_candidate(base_ang + da, base_sc * ds)
                    if sc_val > best_score:
                        best_score = sc_val
                        best_params = (base_ang + da, base_sc * ds, dx, dy)

    # Fine 0.25-deg / 0.5% polish around best_params
    b_ang, b_sc, _, _ = best_params
    for da in (-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0):
        for ds in (0.985, 0.992, 1.0, 1.008, 1.015):
            sc_val, dx, dy = eval_candidate(b_ang + da, b_sc * ds)
            if sc_val > best_score:
                best_score = sc_val
                best_params = (b_ang + da, b_sc * ds, dx, dy)

    return best_params


def align_image_organic(distorted: Image.Image, target_size: int = 512) -> Image.Image:
    """Align distorted canvas back to canonical frame using the organic base pour."""
    work_scale = 0.25  # 128x128 for fast Fourier-Mellin registration
    ref_mask = render_base_pour_mask(size=target_size)
    ref_small = np.array(
        Image.fromarray((ref_mask * 255).astype(np.uint8)).resize(
            (int(target_size * work_scale), int(target_size * work_scale)),
            Image.Resampling.BILINEAR,
        ),
        dtype=np.float32,
    ) / 255.0

    mov_w = int(round(distorted.width * work_scale))
    mov_h = int(round(distorted.height * work_scale))
    mov_small_img = distorted.resize((mov_w, mov_h), Image.Resampling.BILINEAR)
    mov_small = extract_base_pour_score(np.array(mov_small_img))

    ang, sc, dx_s, dy_s = logpolar_fft_register(ref_small, mov_small)
    dx = dx_s / work_scale
    dy = dy_s / work_scale

    # One full-res (512x512) translation polish using FFT cross-correlation
    rad = math.radians(ang)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    cx_src = distorted.width / 2.0 + dx
    cy_src = distorted.height / 2.0 + dy
    cx_dst = target_size / 2.0
    cy_dst = target_size / 2.0
    a, b = sc * cos_a, sc * sin_a
    c = cx_src - (a * cx_dst + b * cy_dst)
    d, e = -sc * sin_a, sc * cos_a
    f = cy_src - (d * cx_dst + e * cy_dst)
    coarse = distorted.transform((target_size, target_size), Image.Transform.AFFINE, (a, b, c, d, e, f), resample=Image.Resampling.BILINEAR)

    coarse_score = extract_base_pour_score(np.array(coarse))
    cc_full = np.real(np.fft.ifft2(np.fft.fft2(coarse_score) * np.conj(np.fft.fft2(ref_mask.astype(np.float32)))))
    iy, ix = np.unravel_index(np.argmax(cc_full), cc_full.shape)
    fy = float(iy if iy <= target_size // 2 else iy - target_size)
    fx = float(ix if ix <= target_size // 2 else ix - target_size)
    if abs(fx) <= 24 and abs(fy) <= 24:
        coarse = coarse.transform((target_size, target_size), Image.Transform.AFFINE, (1, 0, fx, 0, 1, fy), resample=Image.Resampling.BILINEAR)
    return coarse


def build_log_decoder(n_bits: int, size: int = 512, alpha: float = 0.50):
    """Precompute Gram inverse G_inv and per-prime log-attenuation vectors for linear decoding."""
    primes = get_first_k_primes(n_bits)
    base_mask = render_base_pour_mask(size=size)
    l_vecs = []
    for idx, p in enumerate(primes):
        rgb, mask = render_prime_stroke_mask(p, idx, size=size)
        col = rgb.astype(np.float32) / 255.0
        att = (1.0 - alpha) + alpha * col
        l_vecs.append((mask & (~base_mask), -np.log(np.clip(att, 1e-4, 1.0))))

    G = np.zeros((n_bits, n_bits), dtype=np.float64)
    for i in range(n_bits):
        mi, li = l_vecs[i]
        for j in range(i, n_bits):
            mj, lj = l_vecs[j]
            ov = int(np.sum(mi & mj))
            if ov > 0:
                G[i, j] = G[j, i] = ov * float(np.dot(li, lj))
    G_inv = np.linalg.inv(G + 1e-3 * np.eye(n_bits))
    return l_vecs, G_inv


def decode_bits_pollock(img: Image.Image, n_bits: int, size: int = 512, alpha: float = 0.50, precomp=None) -> List[int]:
    """Decode n_bits from a distorted Pollock canvas using Fourier-Mellin alignment + log-attenuation solver."""
    l_vecs, G_inv = precomp if precomp is not None else build_log_decoder(n_bits, size=size, alpha=alpha)
    aligned = align_image_organic(img, target_size=size)
    arr = np.array(aligned, dtype=np.float32)
    res = np.clip(arr / BG_RGB, 1e-3, 1.0)
    L_obs = -np.log(res)
    y = np.array([float(np.sum(L_obs[mi] @ li)) for mi, li in l_vecs], dtype=np.float64)
    b_hat = G_inv @ y
    return [1 if v >= 0.5 else 0 for v in b_hat]


def decode_message_pollock(img: Image.Image, n_bits: int, size: int = 512, alpha: float = 0.50) -> Tuple[str, List[int]]:
    """Decode UTF-8 message from a distorted Pollock canvas."""
    rec_bits = decode_bits_pollock(img, n_bits, size=size, alpha=alpha)
    out_bytes = bytearray()
    for i in range(0, len(rec_bits), 8):
        val = 0
        for b in range(8):
            val = (val << 1) | rec_bits[i + b]
        out_bytes.append(val)
    return out_bytes.decode("utf-8", errors="replace"), rec_bits


def run_monte_carlo(n_bits: int = 128, n_trials: int = 100, size: int = 512, alpha: float = 0.50) -> None:
    """Run Monte Carlo RTS + compression/noise benchmark for random n_bits messages."""
    precomp = build_log_decoder(n_bits, size=size, alpha=alpha)
    rng = np.random.default_rng(2026)
    clean_ok = rts_ok = noise_ok = 0
    clean_bits = rts_bits = noise_bits = 0

    for trial in range(n_trials):
        bits = rng.integers(0, 2, size=n_bits).tolist()
        img = encode_bits_pollock(bits, size=size, alpha=alpha)

        rec_c = decode_bits_pollock(img, n_bits, size=size, alpha=alpha, precomp=precomp)
        mc = sum(a == b for a, b in zip(bits, rec_c))
        clean_bits += mc; clean_ok += (mc == n_bits)

        ang = float(rng.uniform(-180, 180))
        sc = float(rng.uniform(0.80, 1.20))
        sh = (float(rng.uniform(-20, 20)), float(rng.uniform(-20, 20)))

        dist = apply_rts_distortion(img, angle_deg=ang, scale=sc, shift=sh, jpeg_quality=80)
        rec_r = decode_bits_pollock(dist, n_bits, size=size, alpha=alpha, precomp=precomp)
        mr = sum(a == b for a, b in zip(bits, rec_r))
        rts_bits += mr; rts_ok += (mr == n_bits)

        dist_n = apply_rts_distortion(img, angle_deg=ang, scale=sc, shift=sh, noise_std=8.0, seed=trial)
        rec_n = decode_bits_pollock(dist_n, n_bits, size=size, alpha=alpha, precomp=precomp)
        mn = sum(a == b for a, b in zip(bits, rec_n))
        noise_bits += mn; noise_ok += (mn == n_bits)

    print(f"Monte Carlo ({n_bits}-bit, {n_trials} trials, {size}x{size}):")
    print(f"  Clean:             {clean_ok}/{n_trials} exact msgs | {clean_bits}/{n_trials*n_bits} bits ({100*clean_bits/(n_trials*n_bits):.2f}%)")
    print(f"  Random RTS+JPEG80: {rts_ok}/{n_trials} exact msgs | {rts_bits}/{n_trials*n_bits} bits ({100*rts_bits/(n_trials*n_bits):.2f}%)")
    print(f"  Random RTS+Noise8: {noise_ok}/{n_trials} exact msgs | {noise_bits}/{n_trials*n_bits} bits ({100*noise_bits/(n_trials*n_bits):.2f}%)")


if __name__ == "__main__":
    msg = "MathArts"
    canvas_img, true_bits = encode_message_pollock(msg, size=512, alpha=0.50)
    print(f"Encoded '{msg}' ({len(true_bits)} bits, primes 2..{get_first_k_primes(len(true_bits))[-1]}) on 1 canvas (512x512, organic top-skein).")

    scenarios = [
        ("Clean canonical", dict(angle_deg=0.0, scale=1.0, shift=(0, 0), noise_std=0.0, jpeg_quality=None)),
        ("Rotated 27 deg, 0.85x, shifted", dict(angle_deg=27.0, scale=0.85, shift=(18, -14), noise_std=0.0, jpeg_quality=None)),
        ("Rotated 143 deg, 1.15x, JPEG q=80", dict(angle_deg=143.0, scale=1.15, shift=(-22, 15), noise_std=0.0, jpeg_quality=80)),
        ("Rotated -38 deg, Gaussian noise std=8", dict(angle_deg=-38.0, scale=0.95, shift=(10, 12), noise_std=8.0, jpeg_quality=None)),
    ]

    pre64 = build_log_decoder(len(true_bits), size=512, alpha=0.50)
    for label, kw in scenarios:
        distorted = apply_rts_distortion(canvas_img, **kw)
        rec_bits = decode_bits_pollock(distorted, len(true_bits), size=512, alpha=0.50, precomp=pre64)
        out_b = bytearray(int("".join(str(b) for b in rec_bits[i:i+8]), 2) for i in range(0, len(rec_bits), 8))
        rec_msg = out_b.decode("utf-8", errors="replace")
        bit_acc = sum(t == r for t, r in zip(true_bits, rec_bits))
        print(f"  [{label}] -> '{rec_msg}' | bits: {bit_acc}/{len(true_bits)}")

    run_monte_carlo(n_bits=128, n_trials=100, size=512, alpha=0.50)
