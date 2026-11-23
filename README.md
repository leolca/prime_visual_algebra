# Visual Number Algebra

Interactive explorer and verification suite for algebraic and painterly visual representations of natural numbers ($n = 1 \dots 120$), inspired by *Journal of Mathematics and the Arts* research on prime-factor visual patterns.

## Visual Systems

1. **Binary XOR-Convolution** ($\mathbb{F}_2[x,y]/(x^9 - 1, y^9 - 1)$)
   - Assigns odd-weight $9 \times 9$ binary basis tiles to primes and combines them via 2D cyclic XOR-convolution, yielding a true commutative monoid homomorphism $\Phi(a \cdot b) = \Phi(a) \star \Phi(b)$ with 120/120 unique tiles.
   - Supports lossless two-tone and geometric presentations (*Organic Ink*, *Raw Binary*, *Diamond / Woven*, *Radial Mandala*) that remain 100% convertible back to `0/1`.
2. **Pollock Drip-Path Superposition**
   - Seeds a deterministic PRNG (`mulberry32`) per prime factor to paint Jackson Pollock-style drip trajectories and splatters, with multiplicity encoded either as path extent (`steps × e`) or separate strokes.
3. **Klee 1914 Watercolor**
   - Translucent `multiply`-blended watercolor bands with prime-specific widths, pigments, alternating horizontal/vertical orientations, and stroke-width-based wrap-around spacing.
4. **Kandinsky Composition VIII**
   - Composes circles, polygons, semicircles, rings, checkerboards, and line bundles with deterministic colors, fill/outline styles, rotations, and Halton-distributed coordinates.

## Files

- `algebra.py` — Generates collision-free $W \times H$ prime basis tiles and verifies $\Phi(a \cdot b) = \Phi(a) \star \Phi(b)$ (`tiles_data.json`).
- `build_explorer.py` — Builds the standalone interactive viewer `explorer.html` with live multiplication lab, tile factorization breakdown, and SVG/PNG/PDF export.
- `verify_decomposition.py` — Verifies 120/120 image uniqueness and blind top-down layer-peeling factor recovery across $n = 1 \dots 120$.
- `explorer.html` — Self-contained interactive viewer (open directly in any browser).

## Quick Start

```bash
python3 algebra.py
python3 build_explorer.py
python3 verify_decomposition.py
```
