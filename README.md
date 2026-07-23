# Yulissa Benitez — Photography Portfolio

Portfolio site for music &amp; editorial photographer **Yulissa Benitez** — WebGL
covers, a year-based work index, and a decision-graph process for exploring
design directions.

## Usage

```bash
python3 src/build.py     # plain build
# or, with Pillow available (recommended — emits WebP + shrinks GL payloads):
<venv-python> src/build.py
```

Then open **`dist/index.html`** (the promoted landing variant). `dist/menu.html`
is the **decision graph** — every design direction as a node, chosen path in red.
The repo-root `index.html` is a copy of the `MAIN` variant with asset paths
adjusted, so it works from the repo root too.

Keep `dist/` together when copying — gallery pages reference `dist/assets/`.

## Architecture

Two kinds of image delivery, chosen per consumer:

- **Display images** (gallery grids, lightboxes) are real files under
  `dist/assets/img/` — original JPEG + responsive WebP renditions (480/960/1600)
  with `srcset`, `sizes`, and honest lazy loading. Year pages are ~30 KB of HTML.
- **WebGL-sampled images** (hero texture, reel atlas sources, year-cover photos
  and depth maps) stay **inline as `data:` URIs** deliberately: `file://` images
  taint canvases and `texImage2D` from a tainted source throws. Inline copies are
  recompressed to texture-appropriate sizes at build time (the hero keeps full
  fidelity).

Asset emission is incremental (content-hash stamp in `dist/assets/.stamp.json`)
and degrades gracefully without Pillow (JPEG-only, uncompressed GL payload).

## The site

- **Monument intro** — the film reel runs full-bleed behind the name as
  translucent glass (Anton), settling on the hero. Glitch effects fire on their
  own schedule, like signal stutter — never cursor-driven.
- **Work index** — one full-viewport cover per year, each with a bespoke
  treatment grown from its photograph:
  - **2026** — the year reflected in his eye; hover domes the cornea out,
    click dives through the pupil.
  - **2025** — the fisheye stairwell swirls like a drain; click spins you down.
  - **2024** — a folded print; the year sits as a faded red stamp, hovering her
    hand presses wrinkles into the paper, click crumples the sheet into her grip.
- **Year galleries** — calm grids, FLIP lightbox (images fly from their grid
  slot to center and back), caption slots wired for publication/client metadata.

All WebGL degrades to flat photography on context loss, no-WebGL browsers,
and `prefers-reduced-motion`.

## Project layout

```
index.html            # promoted variant, works from repo root
dist/                 # built output (gitignored): variants, pages, assets/, menu.html
src/
  variants/           # one self-contained template per design direction
  pages/              # year gallery pages (2026/2025/2024)
  decisions.json      # the design decision tree (renders as dist/menu.html)
  build.py            # asset pipeline + template fill + menu
  data/
    imgdata.json      # source photos (base64) + hero pointer
    covers.json       # year-cover photos, depth maps, anchor coords
    depthlayers.json  # hero depth map + focal point
    aglyph.json       # Archivo A outline + star (aglyph_anton.json for Anton)
    font_b64.txt      # embedded woff2 (font_anton_b64.txt for Anton)
```

## Process

Design directions are explored as parallel variant files and judged on the
decision graph (`dist/menu.html`), driven by `src/decisions.json` — each choice
opens the next, the chosen path locks left to right. Depth maps for new cover
photos are generated locally with Depth Anything V2.

> Placeholder credits, year membership, and contact details are stand-ins until
> the real selects and metadata land.
