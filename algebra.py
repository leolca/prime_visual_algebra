"""
2D Cyclic XOR-Convolution Visual Algebra for Natural Numbers.

Represents integers n in {1, ..., N} as W x H binary matrices over F_2,
combined via multiplication in the polynomial ring F_2[x, y] / (x^W - 1, y^H - 1).
This yields a true commutative monoid homomorphism:
    Phi(a * b) = Phi(a) * Phi(b)
for all a, b, preserving both commutativity and prime-factor multiplicity.
"""

from __future__ import annotations
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


def primes_up_to(n: int) -> List[int]:
    """Return all primes <= n using the Sieve of Eratosthenes."""
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, is_p in enumerate(sieve) if is_p]


def factorize(n: int) -> Dict[int, int]:
    """Return prime factorization {p: exponent} for n >= 1."""
    factors: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def identity_tile(w: int, h: int) -> int:
    """Return the multiplicative identity tile (single 1 at (0, 0)) as a bitmask."""
    return 1


def coords_to_mask(coords: List[Tuple[int, int]], w: int) -> int:
    """Convert a list of (row, col) coordinates into an integer bitmask."""
    mask = 0
    for r, c in coords:
        mask ^= 1 << (r * w + c)
    return mask


def mask_to_grid(mask: int, w: int, h: int) -> List[List[int]]:
    """Convert a bitmask to a h x w grid of 0s and 1s."""
    return [[(mask >> (r * w + c)) & 1 for c in range(w)] for r in range(h)]


def convolve_xor(a: int, b: int, w: int, h: int) -> int:
    """
    2D cyclic XOR-convolution of two W x H binary tiles (represented as bitmasks).
    Equivalent to polynomial multiplication in F_2[x, y] / (x^W - 1, y^H - 1).
    """
    if a == 0 or b == 0:
        return 0
    # Extract set bit positions of a (usually sparse for small primes)
    result = 0
    # Pre-extract row/col shifts for b
    a_bits = [idx for idx in range(w * h) if (a >> idx) & 1]
    b_bits = [idx for idx in range(w * h) if (b >> idx) & 1]
    if len(b_bits) < len(a_bits):
        a_bits, b_bits = b_bits, a_bits

    for idx_a in a_bits:
        ra, ca = divmod(idx_a, w)
        for idx_b in b_bits:
            rb, cb = divmod(idx_b, w)
            r = (ra + rb) % h
            c = (ca + cb) % w
            result ^= 1 << (r * w + c)
    return result


def generate_prime_basis(
    max_n: int,
    w: int = 9,
    h: int = 9,
    seed: int = 42,
    weight_range: Tuple[int, int] = (3, 5),
) -> Tuple[Dict[int, int], Dict[int, int]]:
    """
    Find a set of odd-weight prime basis tiles such that every n in 1..max_n
    maps to a unique binary tile under 2D cyclic XOR-convolution.

    Returns (prime_tiles, all_tiles) where all_tiles[n] is the bitmask for n.
    """
    rng = random.Random(seed)
    primes = primes_up_to(max_n)
    prime_tiles: Dict[int, int] = {}
    all_tiles: Dict[int, int] = {1: identity_tile(w, h)}
    seen_masks = {all_tiles[1]: 1}

    # Build numbers up to max_n incrementally as we assign each prime.
    # A number n's largest prime factor determines when it first appears.
    by_largest_prime: Dict[int, List[int]] = {p: [] for p in primes}
    for n in range(2, max_n + 1):
        facs = factorize(n)
        lp = max(facs.keys())
        by_largest_prime[lp].append(n)

    all_coords = [(r, c) for r in range(h) for c in range(w)]

    for p in primes:
        # Try candidate tiles for prime p until no collisions with existing tiles
        found = False
        for attempt in range(500):
            # Prefer odd popcount (3 or 5) so tiles are never zero-divisors at (1,1)
            k = rng.choice([w_val for w_val in range(weight_range[0], weight_range[1] + 1) if w_val % 2 == 1])
            chosen = rng.sample(all_coords, k)
            cand_mask = coords_to_mask(chosen, w)
            if cand_mask in seen_masks:
                continue

            # Compute tiles for all numbers whose largest prime factor is p
            temp_new: Dict[int, int] = {}
            temp_seen = set(seen_masks.keys())
            collision = False

            # Process in increasing order so p^2 uses p * p, etc.
            for n in sorted(by_largest_prime[p]):
                if n == p:
                    tile = cand_mask
                else:
                    # n = p * (n // p), and n // p is already in temp_new or all_tiles
                    prev_tile = temp_new.get(n // p)
                    if prev_tile is None:
                        prev_tile = all_tiles[n // p]
                    tile = convolve_xor(prev_tile, cand_mask, w, h)
                if tile == 0 or tile in temp_seen:
                    collision = True
                    break
                temp_new[n] = tile
                temp_seen.add(tile)

            if not collision:
                prime_tiles[p] = cand_mask
                for n, tile in temp_new.items():
                    all_tiles[n] = tile
                    seen_masks[tile] = n
                found = True
                break

        if not found:
            raise RuntimeError(f"Could not find collision-free tile for prime {p} in {w}x{h} grid.")

    return prime_tiles, all_tiles


def verify_homomorphism(all_tiles: Dict[int, int], max_n: int, w: int, h: int) -> None:
    """Verify Phi(a * b) == convolve_xor(Phi(a), Phi(b)) for all a * b <= max_n, and uniqueness."""
    assert len(set(all_tiles.values())) == max_n, "Collision detected!"
    for a in range(1, max_n + 1):
        for b in range(a, max_n // a + 1):
            prod = a * b
            expected = all_tiles[prod]
            actual = convolve_xor(all_tiles[a], all_tiles[b], w, h)
            assert actual == expected, f"Homomorphism failed for {a} * {b} = {prod}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate 2D XOR-convolution visual number tiles.")
    parser.add_argument("--width", type=int, default=9, help="Tile width (odd recommended, default: 9)")
    parser.add_argument("--height", type=int, default=9, help="Tile height (odd recommended, default: 9)")
    parser.add_argument("--max-n", type=int, default=120, help="Maximum integer N (default: 120)")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed (default: 2026)")
    args = parser.parse_args()

    W, H, MAX_N = args.width, args.height, args.max_n
    prime_tiles, all_tiles = generate_prime_basis(MAX_N, W, H, seed=args.seed)
    verify_homomorphism(all_tiles, MAX_N, W, H)

    densities = [bin(all_tiles[n]).count("1") / (W * H) for n in range(1, MAX_N + 1)]
    print(f"Success! {MAX_N} unique {W}x{H} tiles generated.")
    print(f"Homomorphism Phi(a*b) = Phi(a) * Phi(b) verified for all a*b <= {MAX_N}.")
    print(f"Density range: min={min(densities):.1%}, median={sorted(densities)[len(densities)//2]:.1%}, max={max(densities):.1%}")

    # Save data for the interactive explorer
    out = {
        "width": W,
        "height": H,
        "max_n": MAX_N,
        "primes": {str(p): mask for p, mask in prime_tiles.items()},
        "tiles": {
            str(n): {
                "mask": str(all_tiles[n]),  # string to avoid JS 53-bit int precision loss!
                "factors": factorize(n),
                "popcount": bin(all_tiles[n]).count("1"),
            }
            for n in range(1, MAX_N + 1)
        },
    }
    out_path = Path(__file__).parent / "tiles_data.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Saved {out_path}")
