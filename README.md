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
- `build_explorer.py` — Builds the standalone interactive viewer `explorer.html` with live multiplication lab, tile factorization breakdown, Text/Binary/Hex-to-Art codec tab, and SVG/PNG/PDF export.
- `verify_decomposition.py` — Verifies image uniqueness, continuous-space homomorphism checks, and template-invertibility factor recovery across $n = 1 \dots 120$.
- `pollock_codec.py` — Single-canvas $512 \times 512$ Pollock message encoder/decoder with keyed organic registration skein, Fourier--Mellin alignment, `np.linalg.solve` log-attenuation solver, and pure-Python `BCH(127, 92, t=5)` error correction.
- `explorer.html` — Self-contained interactive viewer (open directly in any browser).
- `paper/main.tex` / `paper/main.pdf` — Academic manuscript (*Pollock Visual Algebra: Prime-Factor Drip Paintings with Homomorphic Composition and Geometric Resilience*).
- `paper/report_all_modes.tex` / `paper/report_all_modes.pdf` — Companion technical report covering all visual systems, full empirical constants, PRNG offsets, and raw error histograms.

## Main Results

- **Uniqueness & template-invertibility recovery ($1 \le n \le 120$, $100 \times 100$ RGB):** `100%` (`120/120`) exact-RGB uniqueness and recovery across all four Pollock variants, with `0` homomorphism errors in continuous attenuation space (TMG) and continuous toroidal trajectory space (TTS), and $\le 1$~LSB discrepancy across `306` tested 8-bit RGB pairs (`0.97%` of channels).
- **Extended domains:** `200/200` (`100.0%`) recovery on random integers in $2 \dots 10{,}000$ for Separate Strokes, Path Extent, and TMG; `500/500` (`100.0%`) uniqueness and recovery for TTS on $1 \le n \le 500$; `4/4` primorials and `99/100` (`n ≤ 10^6`) + `250/250` (`r ∈ {2..6}`) on TMG stress tests.
- **Single-canvas message codec ($512 \times 512$, RTS + JPEG $q=80$ / Gaussian noise $\sigma=8$):** `64/64` bits on `"MathArts"`; across `1,000` random trials, `99.74%–99.76%` bit accuracy (`92.3%–92.4%` exact messages at $64$ bits, `87.3%–87.7%` uncoded at $128$ bits); and **`99.00%` (`396/400`)** exact-message recovery (`99.94%–99.95%` bit accuracy) using `BCH(127, 92, t=5)`.

## Reproduction & Environment

Tested with **Python 3.14.8**, **NumPy 2.4.6**, and **Pillow 12.3.0** on an Intel Core i7-13650HX CPU:

```bash
python3 algebra.py              # Generate prime basis tiles
python3 build_explorer.py       # Rebuild explorer.html
python3 verify_decomposition.py # Reproduce Section 4 uniqueness, homomorphism & recovery checks
python3 pollock_codec.py        # Reproduce "MathArts" demo and 100-trial RTS Monte Carlo
```

To rebuild the manuscript and companion technical report:

```bash
cd paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
pdflatex report_all_modes.tex && bibtex report_all_modes && pdflatex report_all_modes.tex && pdflatex report_all_modes.tex
```
