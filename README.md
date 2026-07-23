# Yulissa Benitez — Photography Portfolio

A single-page, fully self-contained portfolio site for music &amp; editorial photographer **Yulissa Benitez**.

## Usage

Open **`index.html`** directly in any browser — everything (photos, font, depth maps) is embedded, so there is no build step or server required.

The site is being explored as several **design variants**. After a rebuild, open
**`dist/index.html`** for a side-by-side menu of every variant; `index.html` at the
repo root is always the currently promoted one (`MAIN` in `src/build.py`).

## Variants

- **01 — cinematic** — depth-map WebGL hero with a 4s pull-back intro, cursor-reactive 3D parallax, chromatic aberration, barrel-lens curve, drifting light-leak, film grain.
- **02 — titles** — movie-title-sequence opening: a film reel of photos and wide-tracked type cards whips past with step-printed motion ghosts and glides down under friction over ~6s — every frame clearer than the last — until the strip stills on the hero, which then breathes into depth (dimensional arrival). The name resolves out of the same blur, driven by reel velocity (Bellantoni, *Type in Motion*). Click or key skips it.
- **03 — monument** — the reel runs full-bleed from frame one with giant stacked YULISSA/BENITEZ type overlaid as translucent dark glass — the blur storm visible through and around the letterforms; as the strip slows the name fades away, handing the frame to the finished still. Nameless at rest, no marquee.

Shared across variants: the Archivo Black name treatment (the **A** carries a star in its counter, revealed with a left-to-right shutter-blur), full-bleed masonry gallery with lightbox, inertia scroll, custom cursor, scroll-progress bar; graceful degradation on touch, no-WebGL, and `prefers-reduced-motion`.

## Project layout

```
index.html            # the promoted variant, self-contained (open this)
dist/                 # built variants + comparison menu (gitignored)
src/
  variants/           # one HTML/CSS/JS template per design, __PLACEHOLDER__ tokens
    01-cinematic.html
    02-titles.html
  build.py            # injects data into every variant -> dist/, promotes MAIN -> index.html
  data/
    imgdata.json      # base64 photos
    depthlayers.json  # hero depth map + focal point
    aglyph.json       # extracted Archivo Black "A" outline + star path
    font_b64.txt      # embedded Archivo Black (woff2, base64)
```

## Rebuild

```bash
python3 src/build.py
```

Rebuilds every variant in `src/variants/` into `dist/`, regenerates the `dist/index.html` menu, and copies the `MAIN` variant to the root `index.html`. Adding a design = duplicate a variant file, rename it (`NN-name.html`), rebuild.

> Placeholder credits, client names, and the contact email are stand-ins to be replaced with real details.
