"""
Generate a self-contained interactive HTML/SVG explorer for the 2D XOR-Convolution
Visual Algebra, embedding tiles_data.json so it works directly via file:// URLs.
"""

from pathlib import Path


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Visual Number Algebra — 2D XOR-Convolution</title>
<style>
  :root {
    --bg: #f6f3ec;
    --panel: #ffffff;
    --ink: #1e242b;
    --muted: #66707a;
    --border: #dfd8cc;
    --accent: #2b4c7e;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 24px;
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--ink);
    line-height: 1.45;
  }
  .container { max-width: 1200px; margin: 0 auto; }
  header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 14px;
  }
  h1 { font-size: 1.45rem; margin: 0; font-weight: 700; letter-spacing: -0.02em; }
  .subtitle { color: var(--muted); font-size: 0.9rem; margin: 4px 0 0; }

  .tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 18px;
  }
  .tab-btn {
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--panel);
    color: var(--ink);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.12s ease, border-color 0.12s ease;
  }
  .tab-btn.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 20px;
    align-items: center;
  }
  .control-group { display: flex; flex-direction: column; gap: 4px; }
  .control-group label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); font-weight: 600; }
  select, input[type="number"] {
    padding: 6px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.9rem;
    background: #fff;
    color: var(--ink);
  }
  .checkbox-row { display: flex; align-items: center; gap: 6px; font-size: 0.88rem; cursor: pointer; padding-top: 16px; }

  .lab {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 22px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 20px;
    align-items: center;
  }
  @media (max-width: 820px) {
    .lab { grid-template-columns: 1fr; }
  }
  .lab-eq {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 14px;
  }
  .lab-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }
  .lab-card .cap { font-size: 0.82rem; color: var(--muted); font-weight: 600; }
  .op { font-size: 1.6rem; font-weight: 700; color: var(--muted); padding: 0 4px; }
  .decomp-panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 22px;
  }
  .decomp-header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 12px;
  }
  .decomp-title { font-weight: 700; font-size: 1rem; }
  .decomp-meta { font-size: 0.85rem; color: var(--muted); }
  .decomp-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
  }
  .inspector {
    border-left: 1px solid var(--border);
    padding-left: 18px;
    font-size: 0.85rem;
    min-width: 240px;
  }
  @media (max-width: 820px) {
    .inspector { border-left: none; border-top: 1px solid var(--border); padding-left: 0; padding-top: 14px; }
  }
  .inspector pre {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.72rem;
    line-height: 1.15;
    background: #f3f1ec;
    padding: 8px 10px;
    border-radius: 6px;
    margin: 8px 0 0;
    overflow-x: auto;
  }
  .export-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
  }
  .btn-sm {
    padding: 5px 10px;
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: #f8f6f1;
    color: var(--ink);
    cursor: pointer;
  }
  .btn-sm:hover { background: #ece8de; border-color: #b8b0a2; }
  @media print {
    body { background: #fff; padding: 0; }
    .tabs, .controls, .export-row { display: none !important; }
    .lab, .tile-card { break-inside: avoid; box-shadow: none; }
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
    gap: 12px;
  }
  .tile-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
  }
  .tile-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    border-color: #b8b0a2;
  }
  .tile-card.selected {
    border: 2px solid var(--accent);
    box-shadow: 0 0 0 2px rgba(43,76,126,0.15);
  }
  .tile-num { font-weight: 700; font-size: 0.92rem; margin-top: 6px; }
  .tile-fac { font-size: 0.72rem; color: var(--muted); text-align: center; }
  .badge {
    display: inline-block;
    font-size: 0.65rem;
    padding: 1px 5px;
    border-radius: 4px;
    margin-left: 4px;
    font-weight: 600;
    vertical-align: middle;
  }
  .badge-prime { background: #e3f2ec; color: #166534; }
  .badge-power { background: #fef3c7; color: #92400e; }
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>Visual Number Algebra</h1>
      <p class="subtitle" id="mainSubtitle">Under the hood: 9×9 binary matrices over &#x1D53D;<sub>2</sub>[x,y]/(x<sup>9</sup>−1, y<sup>9</sup>−1). Every presentation style is 100% lossless and convertible back to 0/1.</p>
    </div>
  </header>

  <div class="tabs">
    <button class="tab-btn active" id="tabXor">1. Binary XOR-Convolution</button>
    <button class="tab-btn" id="tabPollock">2. Pollock Drip-Path Superposition</button>
    <button class="tab-btn" id="tabKlee">3. Klee 1914 Watercolor</button>
    <button class="tab-btn" id="tabKandinsky">4. Kandinsky Composition VIII</button>
    <button class="tab-btn" id="tabCodec">5. Text-to-Art Codec</button>
  </div>

  <div class="controls" id="xorControls">
    <div class="control-group">
      <label for="binaryLaw">Composition Law</label>
      <select id="binaryLaw">
        <option value="xor_homomorphism" selected>2D XOR-Convolution (Homomorphism)</option>
        <option value="or_grammar">Bitwise OR Motifs (Generative Grammar)</option>
      </select>
    </div>
    <div class="control-group">
      <label for="styleSelect">Presentation Style</label>
      <select id="styleSelect">
        <option value="organic">Organic Ink (Connected)</option>
        <option value="binary">Raw Binary (0 / 1)</option>
        <option value="diamond">Diamond / Woven</option>
        <option value="mandala">Radial Mandala</option>
      </select>
    </div>

    <div class="control-group">
      <label for="paletteSelect">Two-Tone Palette (Lossless)</label>
      <select id="paletteSelect">
        <option value="bw">Classic Black &amp; White</option>
        <option value="indigo">Indigo &amp; Cream</option>
        <option value="terracotta">Terracotta &amp; Charcoal</option>
        <option value="blueprint">Cyanotype Blueprint</option>
        <option value="forest">Forest &amp; Warm Gold</option>
        <option value="crimson">Crimson &amp; Ivory</option>
      </select>
    </div>

    <label class="checkbox-row">
      <input id="showRoles" type="checkbox" checked />
      Highlight primes / prime powers
    </label>
  </div>

  <div class="controls" id="pollockControls" style="display:none;">
    <div class="control-group">
      <label for="pollockBg">Canvas Ground</label>
      <select id="pollockBg">
        <option value="#f4efe6">Raw Linen (Cream)</option>
        <option value="#ffffff">Gallery White</option>
        <option value="#1a1c20">Dark Charcoal</option>
      </select>
    </div>
    <div class="control-group">
      <label for="pollockDensity">Drip Complexity</label>
      <select id="pollockDensity">
        <option value="18">Light (18 steps/factor)</option>
        <option value="32" selected>Medium (32 steps/factor)</option>
        <option value="52">Dense (52 steps/factor)</option>
      </select>
    </div>
    <div class="control-group">
      <label for="pollockMultMode">Multiplicity Mode (p<sup>e</sup>)</label>
      <select id="pollockMultMode">
        <option value="extent" selected>Path extent (steps × e)</option>
        <option value="separate">Separate strokes (e paths)</option>
        <option value="glaze">Translucent Multiply (Pixel Homomorphism)</option>
        <option value="trajectory">Trajectory Vector Sum (Path Homomorphism)</option>
      </select>
    </div>
    <label class="checkbox-row">
      <input id="showRolesPollock" type="checkbox" checked />
      Highlight primes / prime powers
    </label>
  </div>

  <div class="controls" id="codecControls" style="display:none;">
    <div class="control-group">
      <label for="codecFormat">Input Format</label>
      <select id="codecFormat">
        <option value="utf8" selected>Text (UTF-8)</option>
        <option value="bin">Binary (0 / 1)</option>
        <option value="hex">Hexadecimal (0–F)</option>
      </select>
    </div>
    <div class="control-group" style="min-width:240px;">
      <label for="codecText" id="codecInputLabel">Text to Encode (UTF-8)</label>
      <input id="codecText" type="text" value="MathArts" maxlength="256" placeholder="Enter text..." style="padding:6px 10px; border:1px solid var(--border); border-radius:6px; font-size:14px;" />
    </div>
    <div class="control-group">
      <label for="codecAlpha">Glaze Opacity (&alpha;)</label>
      <select id="codecAlpha">
        <option value="0.35">0.35 (Subtle)</option>
        <option value="0.50" selected>0.50 (Standard RTS)</option>
        <option value="0.65">0.65 (Deep)</option>
      </select>
    </div>
    <div class="control-group">
      <label for="codecSize">Canvas Size</label>
      <select id="codecSize">
        <option value="384">384 &times; 384</option>
        <option value="512" selected>512 &times; 512</option>
        <option value="768">768 &times; 768</option>
      </select>
    </div>
    <label class="checkbox-row">
      <input id="codecTopSkein" type="checkbox" checked />
      Include top-skein (T<sub>0</sub>)
    </label>
    <div class="control-group" style="min-width:140px;">
      <label for="codecSkeinSeed">Top-Skein Seed</label>
      <div style="display:flex; gap:4px;">
        <input id="codecSkeinSeed" type="text" value="0x20261124" maxlength="16" style="width:105px; padding:5px 8px; border:1px solid var(--border); border-radius:6px; font-family:ui-monospace,monospace; font-size:13px;" />
        <button class="btn-sm" id="btnCodecRandomSeed" type="button" title="Generate random seed">Rand</button>
      </div>
    </div>
    <div class="control-group">
      <label for="codecSkeinColor">Top-Skein Color</label>
      <select id="codecSkeinColor">
        <option value="#8b101c" selected>Venetian Crimson (#8b101c)</option>
        <option value="#163a70">Ultramarine (#163a70)</option>
        <option value="#145233">Forest Viridian (#145233)</option>
        <option value="#5c3317">Burnt Umber (#5c3317)</option>
        <option value="#5b1b59">Deep Plum (#5b1b59)</option>
      </select>
    </div>
    <label class="checkbox-row">
      <input id="codecShowSeedLabel" type="checkbox" />
      Stamp seed text
    </label>
    <div style="display:flex; gap:6px; align-self:flex-end; flex-wrap:wrap;">
      <button class="btn-sm" id="btnCodecDownload" style="padding:7px 12px;">Download PNG</button>
      <button class="btn-sm" id="btnCodecDownloadHiRes" style="padding:7px 12px;">High-Res PNG (2048px)</button>
      <button class="btn-sm" id="btnCodecDownloadSvg" style="padding:7px 12px;">Download SVG</button>
    </div>
  </div>

  <div class="controls" id="kleeControls" style="display:none;">
    <div class="control-group">
      <label for="kleePaper">Paper Ground</label>
      <select id="kleePaper">
        <option value="#f6f0e2" selected>Warm Cotton Rag</option>
        <option value="#faf8f3">Ivory Watercolor</option>
        <option value="#efe6d5">Aged Parchment</option>
      </select>
    </div>
    <div class="control-group">
      <label for="kleeExtent">Stroke Extent / Unit</label>
      <select id="kleeExtent">
        <option value="0.55">Short (0.55× width)</option>
        <option value="0.95" selected>Medium (0.95× width)</option>
        <option value="1.45">Long (1.45× width)</option>
      </select>
    </div>
    <div class="control-group">
      <label for="kleeSpacing">Wrap Jump Spacing</label>
      <select id="kleeSpacing">
        <option value="1.05">Tight (1.05× stroke)</option>
        <option value="1.3" selected>Balanced (1.30× stroke)</option>
        <option value="1.65">Airy (1.65× stroke)</option>
      </select>
    </div>
    <label class="checkbox-row">
      <input id="showRolesKlee" type="checkbox" checked />
      Highlight primes / prime powers
    </label>
  </div>

  <div class="controls" id="kandinskyControls" style="display:none;">
    <div class="control-group">
      <label for="kandinskyGround">Canvas Ground</label>
      <select id="kandinskyGround">
        <option value="#f4ede0" selected>Warm Parchment (Comp. VIII)</option>
        <option value="#faf7f0">Ivory Linen</option>
        <option value="#e9e2d0">Aged Cream</option>
      </select>
    </div>
    <div class="control-group">
      <label for="kandinskyMult">Multiplicity (p<sup>e</sup>)</label>
      <select id="kandinskyMult">
        <option value="echoes" selected>Multiple Figures (pos / rot / size)</option>
        <option value="scale">Size Growth (r × √e)</option>
      </select>
    </div>
    <label class="checkbox-row">
      <input id="showRolesKandinsky" type="checkbox" checked />
      Highlight primes / prime powers
    </label>
  </div>

  <div class="lab">
    <div class="lab-eq">
      <div class="lab-card">
        <div id="svgA"></div>
        <div class="cap">
          a = <input id="inputA" type="number" min="1" max="120" value="6" style="width:62px" />
        </div>
      </div>
      <div class="op">⋆</div>
      <div class="lab-card">
        <div id="svgB"></div>
        <div class="cap">
          b = <input id="inputB" type="number" min="1" max="120" value="10" style="width:62px" />
        </div>
      </div>
      <div class="op">=</div>
      <div class="lab-card">
        <div id="svgC"></div>
        <div class="cap" id="capC">a × b = 60</div>
      </div>
    </div>

    <div class="inspector" id="inspector">
      <div><strong>Tile Inspector</strong> (click any tile below)</div>
      <div id="inspMeta" style="margin-top:4px; color:var(--muted);">Showing n = 60</div>
      <pre id="inspMatrix"></pre>
      <div class="export-row">
        <button class="btn-sm" id="btnExportSvg">Export SVG</button>
        <button class="btn-sm" id="btnExportPng">Export PNG</button>
        <button class="btn-sm" id="btnExportPdf">Save PDF</button>
      </div>
    </div>
  </div>

  <div class="decomp-panel" id="decompPanel">
    <div class="decomp-header">
      <div class="decomp-title" id="decompTitle">Selected Tile Factorization: n = 60</div>
      <div class="decomp-meta" id="decompMeta">2² × 3 × 5</div>
    </div>
    <div class="decomp-row" id="decompRow"></div>
  </div>

  <div class="decomp-panel" id="codecPanel" style="display:none;">
    <div class="decomp-header">
      <div class="decomp-title" id="codecTitle">Single-Canvas Pollock Codec: "MathArts"</div>
      <div class="decomp-meta" id="codecStats">8 bytes &middot; 64 bits &middot; primes 2..311</div>
    </div>
    <div style="display:flex; flex-wrap:wrap; gap:20px; align-items:flex-start; margin-top:12px;">
      <div>
        <canvas id="codecCanvas" width="512" height="512" style="width:420px; max-width:100%; height:auto; border-radius:8px; border:1px solid var(--border); box-shadow:0 2px 10px rgba(0,0,0,0.08); display:block;"></canvas>
      </div>
      <div style="flex:1; min-width:260px;">
        <div style="font-size:13px; color:var(--muted); margin-bottom:8px;">
          Each bit index <em>i</em> with value <code>1</code> glazes a deterministic drip trajectory for prime <em>p<sub>i</sub></em> via Translucent Multiply Glazing (TMG) onto raw linen (<code>#f4efe6</code>). Optional Venetian crimson top-skein <em>T<sub>0</sub></em> (<code>#8b101c</code>) enables Fourier&ndash;Mellin RTS registration without fiducial squares.
        </div>
        <div id="codecBreakdown" style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; line-height:1.55; background:#f8f9fb; border:1px solid var(--border); border-radius:6px; padding:10px 12px; max-height:340px; overflow:auto;"></div>
      </div>
    </div>
  </div>

  <div class="grid" id="grid"></div>
</div>

<script>
const DATA = __TILES_DATA_JSON__;
const W = DATA.width;
const H = DATA.height;

const PALETTES = {
  bw:         { fg: "#111111", bg: "#ffffff" },
  indigo:     { fg: "#1e3a5f", bg: "#f9f5eb" },
  terracotta: { fg: "#c85a32", bg: "#232528" },
  blueprint:  { fg: "#f0f7ff", bg: "#134074" },
  forest:     { fg: "#d4af37", bg: "#1b3b2b" },
  crimson:    { fg: "#9b1c2c", bg: "#fcfaf5" },
};

function convolveXor(maskA, maskB) {
  let res = 0n;
  for (let ra = 0; ra < H; ra++) {
    for (let ca = 0; ca < W; ca++) {
      if ((maskA >> BigInt(ra * W + ca)) & 1n) {
        for (let rb = 0; rb < H; rb++) {
          for (let cb = 0; cb < W; cb++) {
            if ((maskB >> BigInt(rb * W + cb)) & 1n) {
              const r = (ra + rb) % H;
              const c = (ca + cb) % W;
              res ^= 1n << BigInt(r * W + c);
            }
          }
        }
      }
    }
  }
  return res;
}

function getBit(mask, r, c) {
  if (r < 0 || r >= H || c < 0 || c >= W) return 0;
  return Number((mask >> BigInt(r * W + c)) & 1n);
}

function renderTileSVG(mask, sizePx, style, palette) {
  const { fg, bg } = palette;
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("width", sizePx);
  svg.setAttribute("height", sizePx);
  svg.setAttribute("viewBox", `0 0 ${W * 10} ${H * 10}`);
  svg.style.borderRadius = "6px";
  svg.style.display = "block";
  svg.style.border = "1px solid rgba(0,0,0,0.08)";

  const bgRect = document.createElementNS(ns, "rect");
  bgRect.setAttribute("width", W * 10);
  bgRect.setAttribute("height", H * 10);
  bgRect.setAttribute("fill", bg);
  svg.appendChild(bgRect);

  if (style === "binary") {
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < W; c++) {
        if (getBit(mask, r, c)) {
          const rect = document.createElementNS(ns, "rect");
          rect.setAttribute("x", c * 10);
          rect.setAttribute("y", r * 10);
          rect.setAttribute("width", 10);
          rect.setAttribute("height", 10);
          rect.setAttribute("fill", fg);
          svg.appendChild(rect);
        }
      }
    }
  } else if (style === "organic") {
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < W; c++) {
        if (!getBit(mask, r, c)) continue;
        const x = c * 10, y = r * 10;
        const circle = document.createElementNS(ns, "circle");
        circle.setAttribute("cx", x + 5);
        circle.setAttribute("cy", y + 5);
        circle.setAttribute("r", 3.9);
        circle.setAttribute("fill", fg);
        svg.appendChild(circle);

        // Connect to right and bottom neighbors cleanly
        if (getBit(mask, r, c + 1)) {
          const link = document.createElementNS(ns, "rect");
          link.setAttribute("x", x + 5);
          link.setAttribute("y", y + 2.2);
          link.setAttribute("width", 10);
          link.setAttribute("height", 5.6);
          link.setAttribute("fill", fg);
          svg.appendChild(link);
        }
        if (getBit(mask, r + 1, c)) {
          const link = document.createElementNS(ns, "rect");
          link.setAttribute("x", x + 2.2);
          link.setAttribute("y", y + 5);
          link.setAttribute("width", 5.6);
          link.setAttribute("height", 10);
          link.setAttribute("fill", fg);
          svg.appendChild(link);
        }
      }
    }
  } else if (style === "diamond") {
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < W; c++) {
        if (!getBit(mask, r, c)) continue;
        const cx = c * 10 + 5, cy = r * 10 + 5;
        const poly = document.createElementNS(ns, "polygon");
        poly.setAttribute("points", `${cx},${cy - 4.5} ${cx + 4.5},${cy} ${cx},${cy + 4.5} ${cx - 4.5},${cy}`);
        poly.setAttribute("fill", fg);
        svg.appendChild(poly);
      }
    }
  } else if (style === "mandala") {
    const cx = (W * 10) / 2, cy = (H * 10) / 2;
    const maxR = (W * 10) * 0.46;
    const ringW = maxR / H;
    for (let r = 0; r < H; r++) {
      const rIn = r * ringW + 0.5;
      const rOut = (r + 1) * ringW - 0.3;
      for (let c = 0; c < W; c++) {
        if (!getBit(mask, r, c)) continue;
        const a0 = (c / W) * 2 * Math.PI - Math.PI / 2;
        const a1 = ((c + 1) / W) * 2 * Math.PI - Math.PI / 2 - 0.04;
        const x0 = cx + rIn * Math.cos(a0), y0 = cy + rIn * Math.sin(a0);
        const x1 = cx + rOut * Math.cos(a0), y1 = cy + rOut * Math.sin(a0);
        const x2 = cx + rOut * Math.cos(a1), y2 = cy + rOut * Math.sin(a1);
        const x3 = cx + rIn * Math.cos(a1), y3 = cy + rIn * Math.sin(a1);
        const path = document.createElementNS(ns, "path");
        const d = `M ${x0} ${y0} L ${x1} ${y1} A ${rOut} ${rOut} 0 0 1 ${x2} ${y2} L ${x3} ${y3} A ${rIn} ${rIn} 0 0 0 ${x0} ${y0} Z`;
        path.setAttribute("d", d);
        path.setAttribute("fill", fg);
        svg.appendChild(path);
      }
    }
  }
  return svg;
}


function formatFactors(factors) {
  const entries = Object.entries(factors);
  if (entries.length === 0) return "unit";
  return entries.map(([p, e]) => e > 1 ? `${p}^${e}` : p).join(" × ");
}

let activeMode = "xor"; // "xor" | "pollock" | "klee" | "kandinsky"

// --- Pollock Drip-Path Engine ---
function mulberry32(seed) {
  let a = seed >>> 0;
  return function() {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const PRIME_LIST = Object.keys(DATA.primes).map(Number).sort((a, b) => a - b);
const PRIME_INDEX = new Map(PRIME_LIST.map((p, idx) => [p, idx]));

function primeColor(p, occurrence = 1, isDarkBg = false) {
  const idx = PRIME_INDEX.get(p) ?? p;
  const hue = (idx * 137.508 + 18) % 360;
  const sat = 72 + ((idx * 13) % 18);
  const baseLight = isDarkBg ? 58 : 42;
  const light = Math.max(22, Math.min(78, baseLight + ((occurrence - 1) % 3) * (isDarkBg ? 8 : -7)));
  return `hsl(${hue.toFixed(1)}, ${sat}%, ${light}%)`;
}

function generatePollockPrimitives(p, occurrence, sizePx, steps, isDarkBg) {
  const seed = (p * 2654435761) ^ (occurrence * 40503311);
  const rand = mulberry32(seed);
  const color = primeColor(p, occurrence, isDarkBg);

  const margin = sizePx * 0.08;
  const span = sizePx - 2 * margin;
  let x = margin + rand() * span;
  let y = margin + rand() * span;
  let angle = rand() * Math.PI * 2;
  let speed = sizePx * (0.08 + rand() * 0.14);

  const curves = [];
  const dots = [];

  for (let i = 0; i < steps; i++) {
    angle += (rand() - 0.5) * 1.9;
    speed = Math.max(sizePx * 0.03, Math.min(sizePx * 0.25, speed * (0.75 + rand() * 0.55)));
    let nx = x + Math.cos(angle) * speed;
    let ny = y + Math.sin(angle) * speed;

    if (nx < margin || nx > sizePx - margin) {
      angle = Math.PI - angle;
      nx = Math.max(margin, Math.min(sizePx - margin, nx));
    }
    if (ny < margin || ny > sizePx - margin) {
      angle = -angle;
      ny = Math.max(margin, Math.min(sizePx - margin, ny));
    }

    const cx = (x + nx) / 2 + (rand() - 0.5) * speed * 0.45;
    const cy = (y + ny) / 2 + (rand() - 0.5) * speed * 0.45;
    const normSpeed = speed / (sizePx * 0.25);
    const lw = Math.max(0.7, (1.15 - normSpeed) * (sizePx * 0.048));
    const uSpeed = Math.max(0, Math.min(1, (speed - sizePx * 0.03) / (sizePx * 0.22)));
    const pPool = 0.58 - 0.40 * uSpeed;
    const pSpray = 0.08 + 0.34 * uSpeed;

    curves.push({ x, y, cx, cy, nx, ny, lw, alpha: 0.88 });

    if (rand() < pPool) {
      const r = lw * (0.6 + rand() * 1.1);
      dots.push({
        x: nx + (rand() - 0.5) * lw * 1.8,
        y: ny + (rand() - 0.5) * lw * 1.8,
        r,
        alpha: 0.82
      });
    }
    if (rand() < pSpray) {
      const sprayCount = 1 + Math.floor(rand() * 3);
      for (let s = 0; s < sprayCount; s++) {
        dots.push({
          x: nx + (rand() - 0.5) * sizePx * 0.18,
          y: ny + (rand() - 0.5) * sizePx * 0.18,
          r: Math.max(0.5, sizePx * (0.005 + rand() * 0.012)),
          alpha: 0.72
        });
      }
    }

    x = nx;
    y = ny;
  }
  return { color, curves, dots };
}

function getPrimeFourierModes(p) {
  const seed = (p * 2654435761) ^ 0x7f4a7c15;
  const rand = mulberry32(seed);
  const modes = [];
  for (let m = 1; m <= 6; m++) {
    const amp = 0.13 / Math.sqrt(m);
    modes.push({
      fx: 1 + Math.floor(rand() * 7),
      fy: 1 + Math.floor(rand() * 7),
      px: rand() * Math.PI * 2,
      py: rand() * Math.PI * 2,
      ax: amp * (0.6 + 0.8 * rand()),
      ay: amp * (0.6 + 0.8 * rand()),
    });
  }
  return modes;
}

function generateTrajectoryPrimitives(facs, sizePx, steps, isDarkBg) {
  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);
  if (primes.length === 0) return { color: isDarkBg ? "#ddd" : "#222", curves: [], dots: [] };

  // Circular mean of prime hues weighted by exponent e
  let sx = 0, sy = 0;
  for (const p of primes) {
    const idx = PRIME_INDEX.get(p) ?? p;
    const hueRad = (((idx * 137.508 + 18) % 360) * Math.PI) / 180;
    sx += facs[p] * Math.cos(hueRad);
    sy += facs[p] * Math.sin(hueRad);
  }
  const meanHue = ((Math.atan2(sy, sx) * 180) / Math.PI + 360) % 360;
  const color = `hsl(${meanHue.toFixed(1)}, 74%, ${isDarkBg ? 60 : 40}%)`;

  const primeModes = primes.map(p => ({ e: facs[p], modes: getPrimeFourierModes(p) }));
  const numPts = Math.max(60, steps * 2);
  const margin = sizePx * 0.06;
  const span = sizePx - 2 * margin;
  const pts = [];

  for (let i = 0; i <= numPts; i++) {
    const t = i / numPts;
    let dx = 0, dy = 0;
    for (const { e, modes } of primeModes) {
      for (const m of modes) {
        dx += e * m.ax * Math.cos(2 * Math.PI * m.fx * t + m.px);
        dy += e * m.ay * Math.sin(2 * Math.PI * m.fy * t + m.py);
      }
    }
    // Toroidal wrap on [0, 1)^2 preserves the exact additive homomorphism gamma_{a*b} = gamma_a + gamma_b (mod 1)
    const wx = (((0.5 + dx) % 1) + 1) % 1;
    const wy = (((0.5 + dy) % 1) + 1) % 1;
    pts.push([margin + wx * span, margin + wy * span]);
  }

  const curves = [];
  const dots = [];
  const rand = mulberry32(1234567);
  for (let i = 0; i < pts.length - 1; i++) {
    const [x, y] = pts[i];
    const [nx, ny] = pts[i + 1];
    const dist = Math.hypot(nx - x, ny - y);
    // Skip drawing across toroidal wrap jumps
    if (dist > span * 0.45) continue;
    const normSpeed = Math.min(1, dist / (sizePx * 0.10));
    const lw = Math.max(0.7, (1.15 - normSpeed) * (sizePx * 0.036));
    const mx = (x + nx) / 2, my = (y + ny) / 2;
    curves.push({ x, y, cx: mx, cy: my, nx, ny, lw, alpha: 0.88 });
    if (rand() < 0.22) {
      dots.push({ x: nx, y: ny, r: lw * 0.75, alpha: 0.80 });
    }
  }
  return { color, curves, dots };
}

function drawPollockPrimitives(ctx, color, curves, dots, alphaScale = 1.0) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  for (const c of curves) {
    ctx.lineWidth = c.lw;
    ctx.globalAlpha = c.alpha * alphaScale;
    ctx.beginPath();
    ctx.moveTo(c.x, c.y);
    ctx.quadraticCurveTo(c.cx, c.cy, c.nx, c.ny);
    ctx.stroke();
  }
  for (const d of dots) {
    ctx.globalAlpha = d.alpha * alphaScale;
    ctx.beginPath();
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawPollockFactor(ctx, p, occurrence, sizePx, steps, isDarkBg) {
  const { color, curves, dots } = generatePollockPrimitives(p, occurrence, sizePx, steps, isDarkBg);
  drawPollockPrimitives(ctx, color, curves, dots, 1.0);
}

function renderPollockSVG(n, sizePx) {
  const bg = document.getElementById("pollockBg").value;
  const steps = parseInt(document.getElementById("pollockDensity").value, 10);
  const multMode = document.getElementById("pollockMultMode").value;
  const isDarkBg = bg === "#1a1c20";

  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("xmlns", ns);
  svg.setAttribute("width", sizePx);
  svg.setAttribute("height", sizePx);
  svg.setAttribute("viewBox", `0 0 ${sizePx} ${sizePx}`);

  const bgRect = document.createElementNS(ns, "rect");
  bgRect.setAttribute("width", sizePx);
  bgRect.setAttribute("height", sizePx);
  bgRect.setAttribute("fill", bg);
  svg.appendChild(bgRect);

  const facs = DATA.tiles[String(n)] ? DATA.tiles[String(n)].factors : factorizeJS(n);
  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);

  const appendPrimitives = (color, curves, dots, alphaScale, blendMode) => {
    for (const c of curves) {
      const path = document.createElementNS(ns, "path");
      path.setAttribute("d", `M ${c.x.toFixed(2)} ${c.y.toFixed(2)} Q ${c.cx.toFixed(2)} ${c.cy.toFixed(2)} ${c.nx.toFixed(2)} ${c.ny.toFixed(2)}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", color);
      path.setAttribute("stroke-width", c.lw.toFixed(2));
      path.setAttribute("stroke-linecap", "round");
      path.setAttribute("stroke-opacity", (c.alpha * alphaScale).toFixed(3));
      if (blendMode) path.setAttribute("style", `mix-blend-mode: ${blendMode};`);
      svg.appendChild(path);
    }
    for (const d of dots) {
      const circle = document.createElementNS(ns, "circle");
      circle.setAttribute("cx", d.x.toFixed(2));
      circle.setAttribute("cy", d.y.toFixed(2));
      circle.setAttribute("r", d.r.toFixed(2));
      circle.setAttribute("fill", color);
      circle.setAttribute("fill-opacity", (d.alpha * alphaScale).toFixed(3));
      if (blendMode) circle.setAttribute("style", `mix-blend-mode: ${blendMode};`);
      svg.appendChild(circle);
    }
  };

  if (multMode === "trajectory") {
    const { color, curves, dots } = generateTrajectoryPrimitives(facs, sizePx, steps, isDarkBg);
    appendPrimitives(color, curves, dots, 1.0, null);
    return svg;
  }

  for (const p of primes) {
    const exp = facs[p];
    if (multMode === "glaze") {
      const { color, curves, dots } = generatePollockPrimitives(p, 1, sizePx, steps, isDarkBg);
      const blend = isDarkBg ? "screen" : "multiply";
      for (let k = 1; k <= exp; k++) appendPrimitives(color, curves, dots, 0.45, blend);
      continue;
    }
    const layers = multMode === "extent"
      ? [{ k: 1, nSteps: steps * exp }]
      : Array.from({ length: exp }, (_, i) => ({ k: i + 1, nSteps: steps }));

    for (const { k, nSteps } of layers) {
      const { color, curves, dots } = generatePollockPrimitives(p, k, sizePx, nSteps, isDarkBg);
      appendPrimitives(color, curves, dots, 1.0, null);
    }
  }
  return svg;
}

const KLEE_PALETTE = [
  "#c84b31", // terracotta vermilion
  "#2d5f8a", // prussian cerulean
  "#d99b26", // warm ochre
  "#4c7a5b", // olive sage
  "#9e3b5a", // rose madder
  "#6b5b95", // muted violet
  "#d66838", // burnt sienna
  "#3b7a75", // verdigris teal
  "#b8860b", // antique gold
  "#5d4e46", // raw umber
];

function kleeColor(p) {
  const idx = PRIME_INDEX.get(p) ?? p;
  if (idx < KLEE_PALETTE.length) return KLEE_PALETTE[idx];
  const hue = (idx * 137.508 + 24) % 360;
  return `hsl(${hue.toFixed(1)}, 54%, 46%)`;
}

function generateKleeSegments(p, exp, sizePx, unitExtentFrac, jumpMult) {
  const seed = (p * 2654435761) ^ 0x9e3779b9;
  const rand = mulberry32(seed);
  const color = kleeColor(p);

  const margin = sizePx * 0.08;
  const span = sizePx - 2 * margin;
  // Characteristic stroke width per prime
  const strokeW = sizePx * (0.09 + rand() * 0.09);
  const jump = strokeW * jumpMult;
  // Alternate horizontal / vertical by prime index (so 2 is horizontal, 3 is vertical, 5 is horizontal, ...)
  const pIdx = PRIME_INDEX.get(p) ?? p;
  const horizontal = (pIdx % 2 === 0);

  let pos = margin + rand() * span;
  let track = margin + strokeW * 0.5 + rand() * Math.max(1, span - strokeW);
  let remaining = exp * span * unitExtentFrac;

  const segments = [];
  let guard = 0;
  while (remaining > 0.5 && guard < 40) {
    guard++;
    const avail = (margin + span) - pos;
    const segLen = Math.min(remaining, Math.max(2, avail));

    // Build 2 overlapping translucent watercolor wash polygons per segment
    const washes = [];
    for (let w = 0; w < 2; w++) {
      const wobble = () => (rand() - 0.5) * strokeW * 0.14;
      const halfW = strokeW * (0.48 + w * 0.06);
      const pts = [];
      const steps = 5;
      if (horizontal) {
        for (let i = 0; i <= steps; i++) {
          const t = i / steps;
          pts.push([pos + segLen * t + wobble() * 0.3, track - halfW + wobble()]);
        }
        for (let i = steps; i >= 0; i--) {
          const t = i / steps;
          pts.push([pos + segLen * t + wobble() * 0.3, track + halfW + wobble()]);
        }
      } else {
        for (let i = 0; i <= steps; i++) {
          const t = i / steps;
          pts.push([track - halfW + wobble(), pos + segLen * t + wobble() * 0.3]);
        }
        for (let i = steps; i >= 0; i--) {
          const t = i / steps;
          pts.push([track + halfW + wobble(), pos + segLen * t + wobble() * 0.3]);
        }
      }
      washes.push({ pts, alpha: w === 0 ? 0.42 : 0.28 });
    }
    segments.push({ color, washes });

    remaining -= segLen;
    if (remaining > 0.5) {
      // Wrap around to the start and jump by spacing based on stroke width
      pos = margin;
      track += jump;
      if (track > margin + span - strokeW * 0.3) {
        track = margin + ((track - margin) % Math.max(strokeW, span - strokeW * 0.5));
      }
    }
  }
  return { color, strokeW, jump, horizontal, segments };
}

function renderKleeCanvas(n, sizePx) {
  const bg = document.getElementById("kleePaper").value;
  const unitExtentFrac = parseFloat(document.getElementById("kleeExtent").value);
  const jumpMult = parseFloat(document.getElementById("kleeSpacing").value);

  const canvas = document.createElement("canvas");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = sizePx * dpr;
  canvas.height = sizePx * dpr;
  canvas.style.width = sizePx + "px";
  canvas.style.height = sizePx + "px";
  canvas.style.borderRadius = "6px";
  canvas.style.display = "block";
  canvas.style.border = "1px solid rgba(0,0,0,0.1)";

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, sizePx, sizePx);

  const facs = DATA.tiles[String(n)] ? DATA.tiles[String(n)].factors : factorizeJS(n);
  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);

  ctx.save();
  ctx.globalCompositeOperation = "multiply";
  for (const p of primes) {
    const exp = facs[p];
    const { color, segments } = generateKleeSegments(p, exp, sizePx, unitExtentFrac, jumpMult);
    ctx.fillStyle = color;
    for (const seg of segments) {
      for (const wash of seg.washes) {
        ctx.globalAlpha = wash.alpha;
        ctx.beginPath();
        wash.pts.forEach(([x, y], idx) => {
          if (idx === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.closePath();
        ctx.fill();
      }
    }
  }
  ctx.restore();
  return canvas;
}

function renderKleeSVG(n, sizePx) {
  const bg = document.getElementById("kleePaper").value;
  const unitExtentFrac = parseFloat(document.getElementById("kleeExtent").value);
  const jumpMult = parseFloat(document.getElementById("kleeSpacing").value);

  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("xmlns", ns);
  svg.setAttribute("width", sizePx);
  svg.setAttribute("height", sizePx);
  svg.setAttribute("viewBox", `0 0 ${sizePx} ${sizePx}`);

  const bgRect = document.createElementNS(ns, "rect");
  bgRect.setAttribute("width", sizePx);
  bgRect.setAttribute("height", sizePx);
  bgRect.setAttribute("fill", bg);
  svg.appendChild(bgRect);

  const facs = DATA.tiles[String(n)] ? DATA.tiles[String(n)].factors : factorizeJS(n);
  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);

  for (const p of primes) {
    const exp = facs[p];
    const { color, segments } = generateKleeSegments(p, exp, sizePx, unitExtentFrac, jumpMult);
    for (const seg of segments) {
      for (const wash of seg.washes) {
        const poly = document.createElementNS(ns, "polygon");
        poly.setAttribute("points", wash.pts.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" "));
        poly.setAttribute("fill", color);
        poly.setAttribute("fill-opacity", wash.alpha);
        poly.setAttribute("style", "mix-blend-mode: multiply;");
        svg.appendChild(poly);
      }
    }
  }
  return svg;
}

// --- Kandinsky Composition VIII Engine ---
const KANDINSKY_SHAPES = [
  "circle", "triangle", "lineBundle", "semicircle", "rectangle",
  "lozenge", "square", "parallelogram", "hexagon", "heptagon",
  "ring", "checker"
];
const KANDINSKY_STYLES = ["filled+outline", "filled", "outline"];
const KANDINSKY_COLORS = [
  "#1c1d21", // deep ink black
  "#c93b2b", // vermilion red
  "#e0ad24", // cadmium yellow
  "#234f8c", // cobalt blue
  "#2c7a6e", // emerald teal
  "#6a4173", // violet plum
  "#d96b27", // burnt orange
  "#c96e7a", // dusty rose
  "#3b6e8c", // slate cerulean
  "#8c3b2b", // sienna
];

function kandinskyColor(p) {
  const idx = PRIME_INDEX.get(p) ?? p;
  return KANDINSKY_COLORS[idx % KANDINSKY_COLORS.length];
}

function halton(index, base) {
  let result = 0;
  let f = 1 / base;
  let i = index;
  while (i > 0) {
    result += f * (i % base);
    i = Math.floor(i / base);
    f /= base;
  }
  return result;
}

function getKandinskySpec(p, k, exp, sizePx, multMode) {
  const pIdx = PRIME_INDEX.get(p) ?? p;
  const seed = (p * 2654435761) ^ (k * 40503311) ^ 0x517cc1b7;
  const rand = mulberry32(seed);

  const shape = KANDINSKY_SHAPES[pIdx % KANDINSKY_SHAPES.length];
  const baseStyleIdx = Math.floor(pIdx / KANDINSKY_SHAPES.length) % KANDINSKY_STYLES.length;
  const style = KANDINSKY_STYLES[(baseStyleIdx + k - 1) % KANDINSKY_STYLES.length];
  const color = KANDINSKY_COLORS[(pIdx + (k - 1) * 3) % KANDINSKY_COLORS.length];

  // Purely determined by (p, k) so every prime keeps its exact position/rotation/size in all composites
  const margin = sizePx * 0.15;
  const span = sizePx - 2 * margin;
  const hx = (halton(1 + pIdx, 2) + (k - 1) * 0.6180339887) % 1;
  const hy = (halton(1 + pIdx, 3) + (k - 1) * 0.3819660113) % 1;
  const cx = margin + hx * span;
  const cy = margin + hy * span;
  const angle = rand() * Math.PI * 2;
  // Wider dynamic range of sizes for Composition VIII contrast (large anchors + crisp small accents)
  const baseR = sizePx * (0.07 + Math.pow(rand(), 1.4) * 0.17);
  const r = multMode === "scale"
    ? baseR * (0.72 + 0.45 * Math.sqrt(exp))
    : baseR * (k === 1 ? 1.15 : Math.max(0.50, 1.0 - (k - 1) * 0.14));
  const aspect = 0.28 + rand() * 0.40;
  const lw = Math.max(1.0, sizePx * (0.012 + rand() * 0.010));

  return { shape, style, color, cx, cy, angle, r, aspect, lw, k, exp, multMode };
}

function buildPolygonPoints(sides, r, sx = 1, sy = 1, shear = 0) {
  const pts = [];
  for (let i = 0; i < sides; i++) {
    const a = (i / sides) * Math.PI * 2 - Math.PI / 2;
    const x = Math.cos(a) * r * sx;
    const y = Math.sin(a) * r * sy;
    pts.push([x + y * shear, y]);
  }
  return pts;
}

function getShapePoints(shape, r, aspect) {
  if (shape === "triangle") return buildPolygonPoints(3, r * 1.15, 1.0, 1.15, 0.25);
  if (shape === "square") return [[-r, -r], [r, -r], [r, r], [-r, r]].map(([x, y]) => [x * 0.85, y * 0.85]);
  if (shape === "rectangle") return [[-r * 1.35, -r * aspect], [r * 1.35, -r * aspect], [r * 1.35, r * aspect], [-r * 1.35, r * aspect]];
  if (shape === "lozenge") return [[0, -r * 1.2], [r * aspect * 1.5, 0], [0, r * 1.2], [-r * aspect * 1.5, 0]];
  if (shape === "parallelogram") {
    const w = r * 1.2, h = r * aspect, sh = r * 0.45;
    return [[-w + sh, -h], [w + sh, -h], [w - sh, h], [-w - sh, h]];
  }
  if (shape === "hexagon") return buildPolygonPoints(6, r);
  if (shape === "heptagon") return buildPolygonPoints(7, r);
  return null;
}

function drawKandinskyCanvas(ctx, spec, sizePx) {
  const { shape, style, color, cx, cy, angle, r, aspect, lw } = spec;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(angle);
  ctx.lineWidth = lw;
  ctx.lineJoin = "miter";
  ctx.lineCap = "butt";

  const ink = "#18181b";
  const applyPaint = (isLine = false) => {
    if (isLine) {
      ctx.strokeStyle = style === "outline" ? ink : color;
      ctx.globalAlpha = 0.92;
      ctx.stroke();
      return;
    }
    if (style === "filled" || style === "filled+outline") {
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.64;
      ctx.fill();
    }
    if (style === "outline" || style === "filled+outline") {
      ctx.strokeStyle = style === "outline" ? color : ink;
      ctx.globalAlpha = 0.92;
      ctx.stroke();
    }
  };

  if (shape === "lineBundle") {
    const len = Math.max(r * 2.6, sizePx * 0.28);
    ctx.beginPath();
    ctx.moveTo(-len, 0);
    ctx.lineTo(len, 0);
    applyPaint(true);
    // Signature Kandinsky crossbar tick
    ctx.beginPath();
    ctx.moveTo(-len * 0.35, -lw * 3.0);
    ctx.lineTo(-len * 0.35, lw * 3.0);
    applyPaint(true);
    ctx.restore();
    return;
  }

  if (shape === "ring") {
    ctx.beginPath();
    ctx.arc(0, 0, r, 0, Math.PI * 2);
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(1.5, lw * 2.2);
    ctx.globalAlpha = 0.86;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(0, 0, r * 0.52, 0, Math.PI * 2);
    ctx.strokeStyle = ink;
    ctx.lineWidth = lw;
    ctx.stroke();
    ctx.restore();
    return;
  }

  if (shape === "checker") {
    const cell = Math.max(2.5, r * 0.45);
    for (let rr = -1; rr <= 1; rr++) {
      for (let cc = -1; cc <= 1; cc++) {
        if ((rr + cc) % 2 === 0) {
          ctx.fillStyle = color;
          ctx.globalAlpha = 0.78;
          ctx.fillRect(cc * cell - cell / 2, rr * cell - cell / 2, cell, cell);
        }
      }
    }
    ctx.restore();
    return;
  }

  ctx.beginPath();
  if (shape === "circle") {
    ctx.arc(0, 0, r, 0, Math.PI * 2);
  } else if (shape === "semicircle") {
    ctx.arc(0, 0, r, Math.PI, 0);
    ctx.closePath();
  } else {
    const pts = getShapePoints(shape, r, aspect);
    pts.forEach(([x, y], idx) => {
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
  }
  applyPaint(false);
  ctx.restore();
}

function renderKandinskyCanvas(n, sizePx) {
  const bg = document.getElementById("kandinskyGround").value;
  const multMode = document.getElementById("kandinskyMult").value;

  const canvas = document.createElement("canvas");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = sizePx * dpr;
  canvas.height = sizePx * dpr;
  canvas.style.width = sizePx + "px";
  canvas.style.height = sizePx + "px";
  canvas.style.borderRadius = "6px";
  canvas.style.display = "block";
  canvas.style.border = "1px solid rgba(0,0,0,0.1)";

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, sizePx, sizePx);

  const facs = DATA.tiles[String(n)] ? DATA.tiles[String(n)].factors : factorizeJS(n);
  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);
  for (const p of primes) {
    const exp = facs[p];
    const count = multMode === "echoes" ? exp : 1;
    for (let k = 1; k <= count; k++) {
      const spec = getKandinskySpec(p, k, exp, sizePx, multMode);
      drawKandinskyCanvas(ctx, spec, sizePx);
    }
  }
  return canvas;
}

function renderKandinskySVG(n, sizePx) {
  const bg = document.getElementById("kandinskyGround").value;
  const multMode = document.getElementById("kandinskyMult").value;

  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("xmlns", ns);
  svg.setAttribute("width", sizePx);
  svg.setAttribute("height", sizePx);
  svg.setAttribute("viewBox", `0 0 ${sizePx} ${sizePx}`);

  const bgRect = document.createElementNS(ns, "rect");
  bgRect.setAttribute("width", sizePx);
  bgRect.setAttribute("height", sizePx);
  bgRect.setAttribute("fill", bg);
  svg.appendChild(bgRect);

  const facs = DATA.tiles[String(n)] ? DATA.tiles[String(n)].factors : factorizeJS(n);
  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);
  const ink = "#18181b";

  for (const p of primes) {
    const exp = facs[p];
    const count = multMode === "echoes" ? exp : 1;
    for (let k = 1; k <= count; k++) {
      const spec = getKandinskySpec(p, k, exp, sizePx, multMode);
      const { shape, style, color, cx, cy, angle, r, aspect, lw } = spec;
      const g = document.createElementNS(ns, "g");
      const deg = (angle * 180) / Math.PI;
      g.setAttribute("transform", `translate(${cx.toFixed(2)}, ${cy.toFixed(2)}) rotate(${deg.toFixed(2)})`);

      const setFillStroke = (el, isLine = false) => {
        if (isLine) {
          el.setAttribute("fill", "none");
          el.setAttribute("stroke", style === "outline" ? ink : color);
          el.setAttribute("stroke-width", lw.toFixed(2));
          el.setAttribute("stroke-opacity", "0.92");
          return;
        }
        el.setAttribute("fill", (style === "filled" || style === "filled+outline") ? color : "none");
        el.setAttribute("fill-opacity", "0.64");
        if (style === "outline" || style === "filled+outline") {
          el.setAttribute("stroke", style === "outline" ? color : ink);
          el.setAttribute("stroke-width", lw.toFixed(2));
          el.setAttribute("stroke-opacity", "0.92");
        }
      };

      if (shape === "lineBundle") {
        const len = Math.max(r * 2.6, sizePx * 0.28);
        const line = document.createElementNS(ns, "line");
        line.setAttribute("x1", (-len).toFixed(2));
        line.setAttribute("y1", "0");
        line.setAttribute("x2", len.toFixed(2));
        line.setAttribute("y2", "0");
        setFillStroke(line, true);
        g.appendChild(line);

        const tick = document.createElementNS(ns, "line");
        tick.setAttribute("x1", (-len * 0.35).toFixed(2));
        tick.setAttribute("y1", (-lw * 3.0).toFixed(2));
        tick.setAttribute("x2", (-len * 0.35).toFixed(2));
        tick.setAttribute("y2", (lw * 3.0).toFixed(2));
        setFillStroke(tick, true);
        g.appendChild(tick);
        svg.appendChild(g);
        continue;
      }

      if (shape === "ring") {
        const c1 = document.createElementNS(ns, "circle");
        c1.setAttribute("cx", "0"); c1.setAttribute("cy", "0"); c1.setAttribute("r", r.toFixed(2));
        c1.setAttribute("fill", "none"); c1.setAttribute("stroke", color);
        c1.setAttribute("stroke-width", Math.max(1.5, lw * 2.2).toFixed(2)); c1.setAttribute("stroke-opacity", "0.86");
        g.appendChild(c1);
        const c2 = document.createElementNS(ns, "circle");
        c2.setAttribute("cx", "0"); c2.setAttribute("cy", "0"); c2.setAttribute("r", (r * 0.52).toFixed(2));
        c2.setAttribute("fill", "none"); c2.setAttribute("stroke", ink);
        c2.setAttribute("stroke-width", lw.toFixed(2)); c2.setAttribute("stroke-opacity", "0.86");
        g.appendChild(c2);
        svg.appendChild(g);
        continue;
      }

      if (shape === "checker") {
        const cell = Math.max(2.5, r * 0.45);
        for (let rr = -1; rr <= 1; rr++) {
          for (let cc = -1; cc <= 1; cc++) {
            if ((rr + cc) % 2 === 0) {
              const rect = document.createElementNS(ns, "rect");
              rect.setAttribute("x", (cc * cell - cell / 2).toFixed(2));
              rect.setAttribute("y", (rr * cell - cell / 2).toFixed(2));
              rect.setAttribute("width", cell.toFixed(2));
              rect.setAttribute("height", cell.toFixed(2));
              rect.setAttribute("fill", color);
              rect.setAttribute("fill-opacity", "0.78");
              g.appendChild(rect);
            }
          }
        }
        svg.appendChild(g);
        continue;
      }

      let el;
      if (shape === "circle") {
        el = document.createElementNS(ns, "circle");
        el.setAttribute("cx", "0");
        el.setAttribute("cy", "0");
        el.setAttribute("r", r.toFixed(2));
      } else if (shape === "semicircle") {
        el = document.createElementNS(ns, "path");
        el.setAttribute("d", `M ${(-r).toFixed(2)} 0 A ${r.toFixed(2)} ${r.toFixed(2)} 0 0 1 ${r.toFixed(2)} 0 Z`);
      } else {
        el = document.createElementNS(ns, "polygon");
        const pts = getShapePoints(shape, r, aspect);
        el.setAttribute("points", pts.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" "));
      }
      setFillStroke(el, false);
      g.appendChild(el);
      svg.appendChild(g);
    }
  }
  return svg;
}

function factorizeJS(n) {
  const facs = {};
  let d = 2, rem = n;
  while (d * d <= rem) {
    while (rem % d === 0) {
      facs[d] = (facs[d] || 0) + 1;
      rem = Math.floor(rem / d);
    }
    d++;
  }
  if (rem > 1) facs[rem] = (facs[rem] || 0) + 1;
  return facs;
}

function renderPollockCanvas(n, sizePx) {
  const bg = document.getElementById("pollockBg").value;
  const steps = parseInt(document.getElementById("pollockDensity").value, 10);
  const multMode = document.getElementById("pollockMultMode").value;
  const isDarkBg = bg === "#1a1c20";

  const canvas = document.createElement("canvas");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = sizePx * dpr;
  canvas.height = sizePx * dpr;
  canvas.style.width = sizePx + "px";
  canvas.style.height = sizePx + "px";
  canvas.style.borderRadius = "6px";
  canvas.style.display = "block";
  canvas.style.border = "1px solid rgba(0,0,0,0.1)";

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, sizePx, sizePx);

  const facs = DATA.tiles[String(n)] ? DATA.tiles[String(n)].factors : factorizeJS(n);
  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);

  if (multMode === "trajectory") {
    const { color, curves, dots } = generateTrajectoryPrimitives(facs, sizePx, steps, isDarkBg);
    drawPollockPrimitives(ctx, color, curves, dots, 1.0);
    return canvas;
  }

  if (multMode === "glaze") {
    ctx.save();
    ctx.globalCompositeOperation = isDarkBg ? "screen" : "multiply";
    for (const p of primes) {
      const exp = facs[p];
      const { color, curves, dots } = generatePollockPrimitives(p, 1, sizePx, steps, isDarkBg);
      for (let k = 1; k <= exp; k++) {
        drawPollockPrimitives(ctx, color, curves, dots, 0.45);
      }
    }
    ctx.restore();
    return canvas;
  }

  for (const p of primes) {
    const exp = facs[p];
    if (multMode === "extent") {
      drawPollockFactor(ctx, p, 1, sizePx, steps * exp, isDarkBg);
    } else {
      for (let k = 1; k <= exp; k++) {
        drawPollockFactor(ctx, p, k, sizePx, steps, isDarkBg);
      }
    }
  }
  return canvas;
}

function updateInspector(n, mask) {
  inspectedN = n;
  inspectedMask = mask;
  const meta = document.getElementById("inspMeta");
  const pre = document.getElementById("inspMatrix");
  const entry = DATA.tiles[String(n)];
  const facs = entry ? entry.factors : factorizeJS(n);
  const facStr = formatFactors(facs);

  if (activeMode === "kandinsky") {
    const multMode = document.getElementById("kandinskyMult").value;
    const distinctForms = Object.keys(facs).length;
    meta.textContent = `n = ${n} · ${facStr} · ${distinctForms} geometric form(s)`;
    const lines = Object.keys(facs).map(Number).sort((a, b) => a - b).map(p => {
      const e = facs[p];
      const spec = getKandinskySpec(p, 1, e, 100, multMode);
      return `prime ${p}^${e}: ${spec.shape} (${spec.style}, ${spec.color})`;
    });
    pre.textContent = lines.length ? lines.join("\n") : "unit (blank parchment)";
    return;
  }

  if (activeMode === "klee") {
    const distinctColors = Object.keys(facs).length;
    const unitExtent = document.getElementById("kleeExtent").value;
    meta.textContent = `n = ${n} · ${facStr} · ${distinctColors} watercolor wash(es)`;
    const lines = Object.keys(facs).map(Number).sort((a, b) => a - b).map(p => {
      const e = facs[p];
      return `prime ${p}^${e}: extent ${(e * parseFloat(unitExtent)).toFixed(2)}× (${kleeColor(p)})`;
    });
    pre.textContent = lines.length ? lines.join("\n") : "unit (blank cotton rag paper)";
    return;
  }

  if (activeMode === "pollock") {
    const multMode = document.getElementById("pollockMultMode").value;
    const baseSteps = parseInt(document.getElementById("pollockDensity").value, 10);
    const totalPaths = multMode === "extent"
      ? Object.keys(facs).length
      : Object.values(facs).reduce((a, b) => a + b, 0);
    const distinctColors = Object.keys(facs).length;
    meta.textContent = `n = ${n} · ${facStr} · ${totalPaths} path(s), ${distinctColors} color(s)`;
    const lines = Object.keys(facs).map(Number).sort((a, b) => a - b).map(p => {
      const e = facs[p];
      if (multMode === "extent") {
        return `prime ${p}^${e}: 1 path, ${baseSteps * e} steps (${primeColor(p, 1, false)})`;
      }
      return `prime ${p}: ${e} drip path(s) (${primeColor(p, 1, false)})`;
    });
    pre.textContent = lines.length ? lines.join("\n") : "unit (blank primed canvas)";
    return;
  }

  let pop = 0;
  let lines = [];
  for (let r = 0; r < H; r++) {
    let row = [];
    for (let c = 0; c < W; c++) {
      const b = getBit(mask, r, c);
      pop += b;
      row.push(b ? "1" : "·");
    }
    lines.push(row.join(" "));
  }
  meta.textContent = `n = ${n} · ${facStr} · ${pop}/${W*H} bits (${Math.round(100*pop/(W*H))}%)`;
  pre.textContent = lines.join("\n");
}

function renderLab() {
  const a = Math.max(1, Math.min(120, parseInt(document.getElementById("inputA").value || "1", 10)));
  const b = Math.max(1, Math.min(120, parseInt(document.getElementById("inputB").value || "1", 10)));
  const prod = a * b;

  const svgA = document.getElementById("svgA");
  const svgB = document.getElementById("svgB");
  const svgC = document.getElementById("svgC");
  svgA.innerHTML = ""; svgB.innerHTML = ""; svgC.innerHTML = "";

  if (activeMode === "kandinsky") {
    svgA.appendChild(renderKandinskyCanvas(a, 86));
    svgB.appendChild(renderKandinskyCanvas(b, 86));
    svgC.appendChild(renderKandinskyCanvas(prod, 86));
    document.getElementById("capC").textContent = `a × b = ${prod} (forms composed)`;
    updateInspector(prod, 0n);
    return;
  }

  if (activeMode === "klee") {
    svgA.appendChild(renderKleeCanvas(a, 86));
    svgB.appendChild(renderKleeCanvas(b, 86));
    svgC.appendChild(renderKleeCanvas(prod, 86));
    document.getElementById("capC").textContent = `a × b = ${prod} (washes glazed)`;
    updateInspector(prod, 0n);
    return;
  }

  if (activeMode === "pollock") {
    svgA.appendChild(renderPollockCanvas(a, 86));
    svgB.appendChild(renderPollockCanvas(b, 86));
    svgC.appendChild(renderPollockCanvas(prod, 86));
    document.getElementById("capC").textContent = `a × b = ${prod} (paths superimposed)`;
    updateInspector(prod, 0n);
    return;
  }

  const style = document.getElementById("styleSelect").value;
  const palette = PALETTES[document.getElementById("paletteSelect").value];
  const law = document.getElementById("binaryLaw").value;

  if (law === "or_grammar") {
    const maskA = BigInt(DATA.tiles[String(a)].or_mask);
    const maskB = BigInt(DATA.tiles[String(b)].or_mask);
    const facsProd = factorizeJS(prod);
    let maskC = 0n;
    for (const [p, e] of Object.entries(facsProd)) {
      const key = `${p}^${e}`;
      if (DATA.or_pp_tiles[key]) maskC |= BigInt(DATA.or_pp_tiles[key]);
    }
    svgA.appendChild(renderTileSVG(maskA, 86, style, palette));
    svgB.appendChild(renderTileSVG(maskB, 86, style, palette));
    svgC.appendChild(renderTileSVG(maskC, 86, style, palette));
    document.getElementById("capC").textContent = `a × b = ${prod} (OR grammar)`;
    updateInspector(prod, maskC);
    return;
  }

  const maskA = BigInt(DATA.tiles[String(a)].mask);
  const maskB = BigInt(DATA.tiles[String(b)].mask);
  const maskC = convolveXor(maskA, maskB);

  svgA.appendChild(renderTileSVG(maskA, 86, style, palette));
  svgB.appendChild(renderTileSVG(maskB, 86, style, palette));
  svgC.appendChild(renderTileSVG(maskC, 86, style, palette));

  const matchNote = (prod <= DATA.max_n && BigInt(DATA.tiles[String(prod)].mask) === maskC)
    ? " ✓ matches"
    : "";
  document.getElementById("capC").textContent = `a × b = ${prod}${matchNote}`;
  updateInspector(prod, maskC);
}

let selectedN = 60;
let clickTarget = "A";
let inspectedN = 60;
let inspectedMask = 0n;

function renderVisualForN(n, sizePx) {
  if (activeMode === "pollock") return renderPollockCanvas(n, sizePx);
  if (activeMode === "klee") return renderKleeCanvas(n, sizePx);
  if (activeMode === "kandinsky") return renderKandinskyCanvas(n, sizePx);
  const style = document.getElementById("styleSelect").value;
  const palette = PALETTES[document.getElementById("paletteSelect").value];
  const law = document.getElementById("binaryLaw").value;
  const entry = DATA.tiles[String(n)];
  const mask = BigInt(law === "or_grammar" ? entry.or_mask : entry.mask);
  return renderTileSVG(mask, sizePx, style, palette);
}

function renderFactorizationPanel(n) {
  const entry = DATA.tiles[String(n)];
  const facs = entry ? entry.factors : factorizeJS(n);
  const facStr = formatFactors(facs);
  document.getElementById("decompTitle").textContent = `Selected Tile Factorization: n = ${n}`;
  document.getElementById("decompMeta").textContent = n === 1 ? "1 (multiplicative identity)" : `${n} = ${facStr}`;

  const row = document.getElementById("decompRow");
  row.innerHTML = "";

  const targetCard = document.createElement("div");
  targetCard.className = "lab-card";
  targetCard.appendChild(renderVisualForN(n, 84));
  const targetCap = document.createElement("div");
  targetCap.className = "cap";
  targetCap.textContent = `Φ(${n})`;
  targetCard.appendChild(targetCap);
  row.appendChild(targetCard);

  const primes = Object.keys(facs).map(Number).sort((a, b) => a - b);
  if (primes.length === 0) return;

  const eqOp = document.createElement("div");
  eqOp.className = "op";
  eqOp.textContent = "=";
  row.appendChild(eqOp);

  primes.forEach((p, idx) => {
    if (idx > 0) {
      const star = document.createElement("div");
      star.className = "op";
      star.textContent = "⋆";
      row.appendChild(star);
    }
    const exp = facs[p];
    const pp = Math.pow(p, exp);
    const fCard = document.createElement("div");
    fCard.className = "lab-card";
    fCard.appendChild(renderVisualForN(pp, 74));
    const fCap = document.createElement("div");
    fCap.className = "cap";
    fCap.textContent = exp > 1 ? `Φ(${p}^${exp}) = Φ(${pp})` : `Φ(${p})`;
    fCard.appendChild(fCap);
    row.appendChild(fCard);
  });
}

function renderGrid() {
  const grid = document.getElementById("grid");
  const style = document.getElementById("styleSelect").value;
  const palette = PALETTES[document.getElementById("paletteSelect").value];
  const maxN = DATA.max_n;
  const showRoles = activeMode === "pollock"
    ? document.getElementById("showRolesPollock").checked
    : activeMode === "klee"
    ? document.getElementById("showRolesKlee").checked
    : activeMode === "kandinsky"
    ? document.getElementById("showRolesKandinsky").checked
    : document.getElementById("showRoles").checked;

  const law = document.getElementById("binaryLaw").value;
  grid.innerHTML = "";
  for (let n = 1; n <= maxN; n++) {
    const entry = DATA.tiles[String(n)];
    const mask = BigInt(law === "or_grammar" ? entry.or_mask : entry.mask);
    const facs = entry.factors;
    const keys = Object.keys(facs);
    const isPrime = keys.length === 1 && facs[keys[0]] === 1;
    const isPrimePower = keys.length === 1 && facs[keys[0]] > 1;

    const card = document.createElement("div");
    card.className = "tile-card" + (n === selectedN ? " selected" : "");
    if (activeMode === "pollock") {
      card.appendChild(renderPollockCanvas(n, 76));
    } else if (activeMode === "klee") {
      card.appendChild(renderKleeCanvas(n, 76));
    } else if (activeMode === "kandinsky") {
      card.appendChild(renderKandinskyCanvas(n, 76));
    } else {
      card.appendChild(renderTileSVG(mask, 76, style, palette));
    }

    const numDiv = document.createElement("div");
    numDiv.className = "tile-num";
    numDiv.textContent = n;
    if (showRoles && isPrime) {
      const b = document.createElement("span");
      b.className = "badge badge-prime";
      b.textContent = "P";
      numDiv.appendChild(b);
    } else if (showRoles && isPrimePower) {
      const b = document.createElement("span");
      b.className = "badge badge-power";
      b.textContent = "Pᵏ";
      numDiv.appendChild(b);
    }
    card.appendChild(numDiv);

    const facDiv = document.createElement("div");
    facDiv.className = "tile-fac";
    facDiv.textContent = isPrime ? "prime" : formatFactors(facs);
    card.appendChild(facDiv);

    card.addEventListener("click", () => {
      selectedN = n;
      renderFactorizationPanel(n);
      if (clickTarget === "A") {
        document.getElementById("inputA").value = n;
        clickTarget = "B";
      } else {
        document.getElementById("inputB").value = n;
        clickTarget = "A";
      }
      renderLab();
      renderGrid();
    });

    grid.appendChild(card);
  }
}

["binaryLaw", "styleSelect", "paletteSelect", "showRoles", "pollockBg", "pollockDensity", "pollockMultMode", "showRolesPollock", "kleePaper", "kleeExtent", "kleeSpacing", "showRolesKlee", "kandinskyGround", "kandinskyMult", "showRolesKandinsky"].forEach(id => {
  document.getElementById(id).addEventListener("change", () => { renderLab(); renderFactorizationPanel(selectedN); renderGrid(); });
});
["inputA", "inputB"].forEach(id => {
  document.getElementById(id).addEventListener("input", renderLab);
});

function getFirstKPrimes(k) {
  const primes = [];
  let n = 2;
  while (primes.length < k) {
    let isP = true;
    for (let d = 2; d * d <= n; d++) {
      if (n % d === 0) { isP = false; break; }
    }
    if (isP) primes.push(n);
    n++;
  }
  return primes;
}

function hslToRgbArr(h, s, l) {
  const hNorm = ((h % 360) + 360) % 360 / 360;
  const sNorm = s / 100;
  const lNorm = l / 100;
  if (sNorm === 0) {
    const v = Math.round(lNorm * 255);
    return [v, v, v];
  }
  const q = lNorm < 0.5 ? lNorm * (1 + sNorm) : lNorm + sNorm - lNorm * sNorm;
  const p = 2 * lNorm - q;
  const hue2rgb = t => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  return [
    Math.round(hue2rgb(hNorm + 1 / 3) * 255),
    Math.round(hue2rgb(hNorm) * 255),
    Math.round(hue2rgb(hNorm - 1 / 3) * 255),
  ];
}

function hexToRgbArr(hex) {
  const clean = hex.replace("#", "");
  return [
    parseInt(clean.slice(0, 2), 16),
    parseInt(clean.slice(2, 4), 16),
    parseInt(clean.slice(4, 6), 16),
  ];
}

function rgbToHueDeg(rgb) {
  const r = rgb[0] / 255, g = rgb[1] / 255, b = rgb[2] / 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), df = mx - mn;
  if (df < 1e-6) return 0;
  if (mx === r) return ((60 * ((g - b) / df) + 360) % 360);
  if (mx === g) return ((60 * ((b - r) / df) + 120) % 360);
  return ((60 * ((r - g) / df) + 240) % 360);
}

function parseSkeinSeed(str) {
  const s = (str || "").trim();
  if (/^0x[0-9a-fA-F]+$/.test(s)) return (parseInt(s, 16) >>> 0);
  if (/^\d+$/.test(s)) return (parseInt(s, 10) >>> 0);
  // Hash arbitrary string seed via FNV-1a
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h;
}

function primeColorCodec(idx, skeinColorHex = "#8b101c") {
  let hueStart = 28.0;
  if (skeinColorHex.toLowerCase() !== "#8b101c") {
    const skHue = rgbToHueDeg(hexToRgbArr(skeinColorHex));
    hueStart = (skHue + 29.0) % 360.0;
  }
  const hue = (hueStart + ((idx * 137.508) % 302.0)) % 360.0;
  const sat = 66.0 + ((idx * 13) % 18);
  const light = 43.0;
  return hslToRgbArr(hue, sat, light);
}

function computeCodecStrokePrimitives(seed, size, steps, marginFrac, lwScale) {
  const rand = mulberry32(seed >>> 0);
  const margin = size * marginFrac;
  const span = size - 2 * margin;
  let x = margin + rand() * span;
  let y = margin + rand() * span;
  let angle = rand() * Math.PI * 2;
  let speed = size * (0.06 + rand() * 0.11);

  const segments = [];
  const droplets = [];
  for (let i = 0; i < steps; i++) {
    angle += (rand() - 0.5) * 1.9;
    speed = Math.max(size * 0.025, Math.min(size * 0.18, speed * (0.75 + rand() * 0.55)));
    let nx = x + Math.cos(angle) * speed;
    let ny = y + Math.sin(angle) * speed;
    if (nx < margin || nx > size - margin) {
      angle = Math.PI - angle;
      nx = Math.max(margin, Math.min(size - margin, nx));
    }
    if (ny < margin || ny > size - margin) {
      angle = -angle;
      ny = Math.max(margin, Math.min(size - margin, ny));
    }
    const cx = (x + nx) / 2 + (rand() - 0.5) * speed * 0.45;
    const cy = (y + ny) / 2 + (rand() - 0.5) * speed * 0.45;
    const lw = Math.max(2, Math.round((1.15 - speed / (size * 0.18)) * size * lwScale));
    segments.push({ x, y, cx, cy, nx, ny, lw });

    if (rand() < 0.35) {
      const rr = lw * (0.6 + rand() * 0.9);
      const ox = nx + (rand() - 0.5) * lw * 1.6;
      const oy = ny + (rand() - 0.5) * lw * 1.6;
      droplets.push({ ox, oy, rr });
    }
    x = nx;
    y = ny;
  }
  return { segments, droplets };
}

function renderCodecStrokeMask(seed, size, steps, marginFrac, lwScale) {
  const off = document.createElement("canvas");
  off.width = size;
  off.height = size;
  const ctx = off.getContext("2d");
  ctx.clearRect(0, 0, size, size);
  ctx.strokeStyle = "#ffffff";
  ctx.fillStyle = "#ffffff";
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  const { segments, droplets } = computeCodecStrokePrimitives(seed, size, steps, marginFrac, lwScale);
  for (const s of segments) {
    ctx.lineWidth = s.lw;
    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.quadraticCurveTo(s.cx, s.cy, s.nx, s.ny);
    ctx.stroke();
  }
  for (const d of droplets) {
    ctx.beginPath();
    ctx.arc(d.ox, d.oy, d.rr, 0, Math.PI * 2);
    ctx.fill();
  }
  return ctx.getImageData(0, 0, size, size).data;
}

function renderCodecToCanvas(canvas, size, bits, primes, alpha, useTopSkein, skeinSeed, skeinRgb, skeinColorHex, showSeedLabel) {
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");

  const nPix = size * size;
  const buf = new Float32Array(nPix * 3);
  for (let i = 0; i < nPix; i++) {
    buf[i * 3] = 244;
    buf[i * 3 + 1] = 239;
    buf[i * 3 + 2] = 230;
  }

  let onesCount = 0;
  for (let idx = 0; idx < bits.length; idx++) {
    if (bits[idx] !== 1) continue;
    onesCount++;
    const p = primes[idx];
    const seed = (Math.imul(p, 2654435761) ^ 0x40503311) >>> 0;
    const maskData = renderCodecStrokeMask(seed, size, 28, 0.10, 0.022);
    const rgb = primeColorCodec(idx, skeinColorHex);
    const f0 = (1.0 - alpha) + alpha * (rgb[0] / 255.0);
    const f1 = (1.0 - alpha) + alpha * (rgb[1] / 255.0);
    const f2 = (1.0 - alpha) + alpha * (rgb[2] / 255.0);
    for (let i = 0; i < nPix; i++) {
      if (maskData[i * 4 + 3] > 64) {
        buf[i * 3] *= f0;
        buf[i * 3 + 1] *= f1;
        buf[i * 3 + 2] *= f2;
      }
    }
  }

  if (useTopSkein) {
    const skeinData = renderCodecStrokeMask(skeinSeed, size, 26, 0.12, 0.028);
    for (let i = 0; i < nPix; i++) {
      if (skeinData[i * 4 + 3] > 64) {
        buf[i * 3] = skeinRgb[0];
        buf[i * 3 + 1] = skeinRgb[1];
        buf[i * 3 + 2] = skeinRgb[2];
      }
    }
  }

  const outImg = ctx.createImageData(size, size);
  for (let i = 0; i < nPix; i++) {
    outImg.data[i * 4] = Math.max(0, Math.min(255, Math.round(buf[i * 3])));
    outImg.data[i * 4 + 1] = Math.max(0, Math.min(255, Math.round(buf[i * 3 + 1])));
    outImg.data[i * 4 + 2] = Math.max(0, Math.min(255, Math.round(buf[i * 3 + 2])));
    outImg.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(outImg, 0, 0);

  if (useTopSkein && showSeedLabel) {
    const hexTag = "0x" + skeinSeed.toString(16).padStart(8, "0");
    ctx.save();
    ctx.font = `${Math.max(10, Math.round(size * 0.022))}px ui-monospace, Menlo, monospace`;
    ctx.fillStyle = "rgba(40, 35, 30, 0.55)";
    ctx.textAlign = "right";
    ctx.textBaseline = "bottom";
    ctx.fillText(`T0: ${hexTag}`, size - Math.round(size * 0.025), size - Math.round(size * 0.02));
    ctx.restore();
  }
  return onesCount;
}

function buildCodecSVG(size, bits, primes, alpha, useTopSkein, skeinSeed, skeinColorHex, showSeedLabel) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("xmlns", ns);
  svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
  svg.setAttribute("width", String(size));
  svg.setAttribute("height", String(size));

  const bg = document.createElementNS(ns, "rect");
  bg.setAttribute("width", String(size));
  bg.setAttribute("height", String(size));
  bg.setAttribute("fill", "#f4efe6");
  svg.appendChild(bg);

  const appendStrokeGroup = (seed, steps, marginFrac, lwScale, colorStr, blendMultiply) => {
    const g = document.createElementNS(ns, "g");
    if (blendMultiply) g.setAttribute("style", "mix-blend-mode: multiply;");
    const { segments, droplets } = computeCodecStrokePrimitives(seed, size, steps, marginFrac, lwScale);
    for (const s of segments) {
      const path = document.createElementNS(ns, "path");
      path.setAttribute("d", `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} Q ${s.cx.toFixed(2)} ${s.cy.toFixed(2)} ${s.nx.toFixed(2)} ${s.ny.toFixed(2)}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", colorStr);
      path.setAttribute("stroke-width", String(s.lw));
      path.setAttribute("stroke-linecap", "round");
      path.setAttribute("stroke-linejoin", "round");
      g.appendChild(path);
    }
    for (const d of droplets) {
      const c = document.createElementNS(ns, "circle");
      c.setAttribute("cx", d.ox.toFixed(2));
      c.setAttribute("cy", d.oy.toFixed(2));
      c.setAttribute("r", d.rr.toFixed(2));
      c.setAttribute("fill", colorStr);
      g.appendChild(c);
    }
    svg.appendChild(g);
  };

  for (let idx = 0; idx < bits.length; idx++) {
    if (bits[idx] !== 1) continue;
    const p = primes[idx];
    const seed = (Math.imul(p, 2654435761) ^ 0x40503311) >>> 0;
    const rgb = primeColorCodec(idx, skeinColorHex);
    const rAtt = Math.round((1.0 - alpha) * 255 + alpha * rgb[0]);
    const gAtt = Math.round((1.0 - alpha) * 255 + alpha * rgb[1]);
    const bAtt = Math.round((1.0 - alpha) * 255 + alpha * rgb[2]);
    appendStrokeGroup(seed, 28, 0.10, 0.022, `rgb(${rAtt},${gAtt},${bAtt})`, true);
  }

  if (useTopSkein) {
    appendStrokeGroup(skeinSeed, 26, 0.12, 0.028, skeinColorHex, false);
    if (showSeedLabel) {
      const hexTag = "0x" + skeinSeed.toString(16).padStart(8, "0");
      const txt = document.createElementNS(ns, "text");
      txt.setAttribute("x", String(size - Math.round(size * 0.025)));
      txt.setAttribute("y", String(size - Math.round(size * 0.02)));
      txt.setAttribute("text-anchor", "end");
      txt.setAttribute("fill", "rgba(40, 35, 30, 0.55)");
      txt.setAttribute("font-family", "ui-monospace, Menlo, monospace");
      txt.setAttribute("font-size", String(Math.max(10, Math.round(size * 0.022))));
      txt.textContent = `T0: ${hexTag}`;
      svg.appendChild(txt);
    }
  }
  return svg;
}

function parseCodecInput(format, raw) {
  if (format === "bin") {
    const clean = raw.replace(/\s+/g, "");
    if (!/^[01]*$/.test(clean)) {
      return { error: "Binary input may only contain 0, 1, and spaces.", bits: [], label: "Binary" };
    }
    const bits = Array.from(clean, ch => (ch === "1" ? 1 : 0));
    return { error: null, bits, label: "Binary", clean };
  }
  if (format === "hex") {
    const clean = raw.replace(/\s+/g, "").replace(/^0x/i, "");
    if (!/^[0-9a-fA-F]*$/.test(clean)) {
      return { error: "Hexadecimal input may only contain 0–9, A–F, and spaces.", bits: [], label: "Hex" };
    }
    const bits = [];
    for (const ch of clean) {
      const nib = parseInt(ch, 16);
      for (let b = 3; b >= 0; b--) {
        bits.push((nib >> b) & 1);
      }
    }
    return { error: null, bits, label: "Hex", clean: clean.toUpperCase() };
  }
  const bytes = new TextEncoder().encode(raw);
  const bits = [];
  for (const byte of bytes) {
    for (let b = 7; b >= 0; b--) {
      bits.push((byte >> b) & 1);
    }
  }
  return { error: null, bits, label: "UTF-8", bytes };
}

function renderCodecArt() {
  const format = document.getElementById("codecFormat").value;
  const text = document.getElementById("codecText").value;
  const alpha = parseFloat(document.getElementById("codecAlpha").value);
  const size = parseInt(document.getElementById("codecSize").value, 10);
  const useTopSkein = document.getElementById("codecTopSkein").checked;
  const seedRaw = document.getElementById("codecSkeinSeed").value;
  const skeinSeed = parseSkeinSeed(seedRaw);
  const skeinColorHex = document.getElementById("codecSkeinColor").value;
  const skeinRgb = hexToRgbArr(skeinColorHex);
  const showSeedLabel = document.getElementById("codecShowSeedLabel").checked;

  const parsed = parseCodecInput(format, text);
  const bits = parsed.bits;
  const primes = getFirstKPrimes(bits.length);
  const canvas = document.getElementById("codecCanvas");
  const onesCount = renderCodecToCanvas(
    canvas, size, bits, primes, alpha, useTopSkein, skeinSeed, skeinRgb, skeinColorHex, showSeedLabel
  );

  const safeTitle = text.length > 0 ? text : "(empty)";
  document.getElementById("codecTitle").textContent = `Single-Canvas Pollock Codec (${parsed.label}): "${safeTitle}"`;
  const breakdownEl = document.getElementById("codecBreakdown");

  if (parsed.error) {
    document.getElementById("codecStats").textContent = "Invalid input";
    breakdownEl.innerHTML = `<span style='color:#b91c1c; font-weight:600;'>${parsed.error}</span>`;
    return;
  }

  const primeSpan = primes.length > 0 ? `2..${primes[primes.length - 1]}` : "none";
  const byteSummary = format === "utf8"
    ? `${parsed.bytes.length} bytes · `
    : format === "hex"
    ? `${(bits.length / 8).toFixed(bits.length % 8 === 0 ? 0 : 1)} bytes · `
    : "";
  document.getElementById("codecStats").textContent =
    `${byteSummary}${bits.length} bits (${onesCount} active strokes) · primes ${primeSpan}`;

  if (bits.length === 0) {
    breakdownEl.innerHTML = "<span style='color:var(--muted);'>Enter text, binary, or hex above to encode bits as prime-indexed Pollock glazes.</span>";
  } else if (format === "utf8") {
    const lines = [];
    for (let bi = 0; bi < parsed.bytes.length; bi++) {
      const bVal = parsed.bytes[bi];
      const ch = (bVal >= 32 && bVal <= 126) ? String.fromCharCode(bVal) : `0x${bVal.toString(16).padStart(2, "0")}`;
      const bStr = bVal.toString(2).padStart(8, "0");
      const activePs = [];
      for (let k = 0; k < 8; k++) {
        if (bStr[k] === "1") activePs.push(primes[bi * 8 + k]);
      }
      lines.push(`<div><strong>${ch.replace(/&/g,"&amp;").replace(/</g,"&lt;")}</strong> (${bStr}) &rarr; primes [${activePs.join(", ") || "none"}]</div>`);
    }
    breakdownEl.innerHTML = lines.join("");
  } else if (format === "hex") {
    const lines = [];
    for (let i = 0; i < parsed.clean.length; i += 2) {
      const chunk = parsed.clean.slice(i, i + 2);
      const bitStart = i * 4;
      const bitEnd = Math.min(bits.length, bitStart + chunk.length * 4);
      const bStr = bits.slice(bitStart, bitEnd).join("");
      const activePs = [];
      for (let k = bitStart; k < bitEnd; k++) {
        if (bits[k] === 1) activePs.push(primes[k]);
      }
      lines.push(`<div><strong>0x${chunk}</strong> (${bStr}) &rarr; primes [${activePs.join(", ") || "none"}]</div>`);
    }
    breakdownEl.innerHTML = lines.join("");
  } else {
    const lines = [];
    for (let i = 0; i < bits.length; i += 8) {
      const slice = bits.slice(i, i + 8);
      const bStr = slice.join("");
      const activePs = [];
      for (let k = 0; k < slice.length; k++) {
        if (slice[k] === 1) activePs.push(primes[i + k]);
      }
      lines.push(`<div><strong>bits[${i}..${i + slice.length - 1}]</strong> (${bStr}) &rarr; primes [${activePs.join(", ") || "none"}]</div>`);
    }
    breakdownEl.innerHTML = lines.join("");
  }
}

function setMode(mode) {
  activeMode = mode;
  document.getElementById("tabXor").classList.toggle("active", mode === "xor");
  document.getElementById("tabPollock").classList.toggle("active", mode === "pollock");
  document.getElementById("tabKlee").classList.toggle("active", mode === "klee");
  document.getElementById("tabKandinsky").classList.toggle("active", mode === "kandinsky");
  document.getElementById("tabCodec").classList.toggle("active", mode === "codec");
  document.getElementById("xorControls").style.display = mode === "xor" ? "flex" : "none";
  document.getElementById("pollockControls").style.display = mode === "pollock" ? "flex" : "none";
  document.getElementById("kleeControls").style.display = mode === "klee" ? "flex" : "none";
  document.getElementById("kandinskyControls").style.display = mode === "kandinsky" ? "flex" : "none";
  document.getElementById("codecControls").style.display = mode === "codec" ? "flex" : "none";

  const isCodec = mode === "codec";
  document.querySelector(".lab").style.display = isCodec ? "none" : "grid";
  document.getElementById("decompPanel").style.display = isCodec ? "none" : "block";
  document.getElementById("grid").style.display = isCodec ? "none" : "grid";
  document.getElementById("codecPanel").style.display = isCodec ? "block" : "none";

  document.getElementById("mainSubtitle").innerHTML = mode === "xor"
    ? 'Under the hood: 9×9 binary matrices over &#x1D53D;<sub>2</sub>[x,y]/(x<sup>9</sup>−1, y<sup>9</sup>−1). Every presentation style is 100% lossless and convertible back to 0/1.'
    : mode === "pollock"
    ? 'Each prime factor seeds a deterministic PRNG with its own color and Jackson Pollock-style drip path; composites superimpose their factor paths.'
    : mode === "klee"
    ? 'Inspired by Paul Klee (1914): each prime factor paints a translucent watercolor band with its own width, color, and starting point, wrapping with stroke-width spacing.'
    : mode === "kandinsky"
    ? 'Inspired by Kandinsky (Composition VIII, 1923): each prime maps to a geometric form (circles, polygons, line bundles, semicircles) with outline/fill/rotation and concentric multiplicity.'
    : 'Single-canvas Text-to-Art Codec: encodes arbitrary UTF-8 text as prime-indexed Translucent Multiply Glazes with an optional Venetian crimson top-skein for RTS registration.';

  if (isCodec) {
    renderCodecArt();
  } else {
    renderLab();
    renderFactorizationPanel(selectedN);
    renderGrid();
  }
}

document.getElementById("tabXor").addEventListener("click", () => setMode("xor"));
document.getElementById("tabPollock").addEventListener("click", () => setMode("pollock"));
document.getElementById("tabKlee").addEventListener("click", () => setMode("klee"));
document.getElementById("tabKandinsky").addEventListener("click", () => setMode("kandinsky"));
document.getElementById("tabCodec").addEventListener("click", () => setMode("codec"));
document.getElementById("codecFormat").addEventListener("change", () => {
  const fmt = document.getElementById("codecFormat").value;
  const lbl = document.getElementById("codecInputLabel");
  const inp = document.getElementById("codecText");
  if (fmt === "bin") {
    lbl.textContent = "Binary to Encode (0 / 1)";
    inp.placeholder = "e.g. 10110010 01011100";
    if (inp.value === "MathArts" || /^[0-9a-fA-F]+$/.test(inp.value.replace(/^0x/i, ""))) {
      if (inp.value === "MathArts") inp.value = "01001101 01100001";
    }
  } else if (fmt === "hex") {
    lbl.textContent = "Hexadecimal to Encode (0–F)";
    inp.placeholder = "e.g. 4D61746841727473";
    if (inp.value === "MathArts" || /^[01\s]+$/.test(inp.value)) {
      inp.value = "4D61746841727473";
    }
  } else {
    lbl.textContent = "Text to Encode (UTF-8)";
    inp.placeholder = "Enter text...";
    if (inp.value === "01001101 01100001" || inp.value === "4D61746841727473") {
      inp.value = "MathArts";
    }
  }
  renderCodecArt();
});
document.getElementById("codecText").addEventListener("input", renderCodecArt);
document.getElementById("codecSkeinSeed").addEventListener("input", renderCodecArt);
document.getElementById("btnCodecRandomSeed").addEventListener("click", () => {
  const r = (Math.floor(Math.random() * 0xffffffff) >>> 0).toString(16).padStart(8, "0");
  document.getElementById("codecSkeinSeed").value = "0x" + r;
  renderCodecArt();
});
["codecAlpha", "codecSize", "codecTopSkein", "codecSkeinColor", "codecShowSeedLabel"].forEach(id => {
  document.getElementById(id).addEventListener("change", renderCodecArt);
});
function getCodecSlug() {
  const raw = document.getElementById("codecText").value || "empty";
  return raw.replace(/[^a-zA-Z0-9_-]+/g, "_").slice(0, 24) || "text";
}

document.getElementById("btnCodecDownload").addEventListener("click", () => {
  const canvas = document.getElementById("codecCanvas");
  canvas.toBlob(blob => {
    if (blob) triggerDownload(blob, `pollock_codec_${getCodecSlug()}.png`);
  }, "image/png");
});

document.getElementById("btnCodecDownloadHiRes").addEventListener("click", () => {
  const format = document.getElementById("codecFormat").value;
  const text = document.getElementById("codecText").value;
  const parsed = parseCodecInput(format, text);
  if (parsed.error) return;
  const bits = parsed.bits;
  const primes = getFirstKPrimes(bits.length);
  const alpha = parseFloat(document.getElementById("codecAlpha").value);
  const useTopSkein = document.getElementById("codecTopSkein").checked;
  const skeinSeed = parseSkeinSeed(document.getElementById("codecSkeinSeed").value);
  const skeinColorHex = document.getElementById("codecSkeinColor").value;
  const skeinRgb = hexToRgbArr(skeinColorHex);
  const showSeedLabel = document.getElementById("codecShowSeedLabel").checked;

  const hiRes = document.createElement("canvas");
  renderCodecToCanvas(
    hiRes, 2048, bits, primes, alpha, useTopSkein, skeinSeed, skeinRgb, skeinColorHex, showSeedLabel
  );
  hiRes.toBlob(blob => {
    if (blob) triggerDownload(blob, `pollock_codec_${getCodecSlug()}_2048px.png`);
  }, "image/png");
});

document.getElementById("btnCodecDownloadSvg").addEventListener("click", () => {
  const format = document.getElementById("codecFormat").value;
  const text = document.getElementById("codecText").value;
  const parsed = parseCodecInput(format, text);
  if (parsed.error) return;
  const bits = parsed.bits;
  const primes = getFirstKPrimes(bits.length);
  const alpha = parseFloat(document.getElementById("codecAlpha").value);
  const size = parseInt(document.getElementById("codecSize").value, 10);
  const useTopSkein = document.getElementById("codecTopSkein").checked;
  const skeinSeed = parseSkeinSeed(document.getElementById("codecSkeinSeed").value);
  const skeinColorHex = document.getElementById("codecSkeinColor").value;
  const showSeedLabel = document.getElementById("codecShowSeedLabel").checked;

  const svg = buildCodecSVG(size, bits, primes, alpha, useTopSkein, skeinSeed, skeinColorHex, showSeedLabel);
  const str = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([str], { type: "image/svg+xml;charset=utf-8" });
  triggerDownload(blob, `pollock_codec_${getCodecSlug()}.svg`);
});

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function getInspectedSVG(sizePx) {
  if (activeMode === "kandinsky") {
    return renderKandinskySVG(inspectedN, sizePx);
  }
  if (activeMode === "klee") {
    return renderKleeSVG(inspectedN, sizePx);
  }
  if (activeMode === "pollock") {
    return renderPollockSVG(inspectedN, sizePx);
  }
  const style = document.getElementById("styleSelect").value;
  const palette = PALETTES[document.getElementById("paletteSelect").value];
  const svg = renderTileSVG(inspectedMask, sizePx, style, palette);
  svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  return svg;
}


document.getElementById("btnExportSvg").addEventListener("click", () => {
  const svg = getInspectedSVG(600);
  const str = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([str], { type: "image/svg+xml;charset=utf-8" });
  triggerDownload(blob, `number_${inspectedN}_${activeMode}.svg`);
});

document.getElementById("btnExportPng").addEventListener("click", () => {
  const size = 800;
  const svg = getInspectedSVG(size);
  const str = new XMLSerializer().serializeToString(svg);
  const svgBlob = new Blob([str], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(svgBlob);
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, size, size);
    URL.revokeObjectURL(url);
    canvas.toBlob(pngBlob => {
      if (pngBlob) triggerDownload(pngBlob, `number_${inspectedN}_${activeMode}.png`);
    }, "image/png");
  };
  img.src = url;
});

document.getElementById("btnExportPdf").addEventListener("click", () => {
  window.print();
});

renderLab();
renderFactorizationPanel(selectedN);
renderGrid();
</script>
</body>
</html>
"""


def main() -> None:
    root = Path(__file__).parent
    data_json = (root / "tiles_data.json").read_text()
    html = HTML_TEMPLATE.replace("__TILES_DATA_JSON__", data_json)
    out_path = root / "explorer.html"
    out_path.write_text(html)
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
