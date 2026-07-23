# Yulissa Benitez — Photography Portfolio

A single-page, fully self-contained portfolio site for music &amp; editorial photographer **Yulissa Benitez**.

## Usage

Open **`index.html`** directly in any browser — everything (photos, font, depth maps) is embedded, so there is no build step or server required.

## Highlights

- **Cinematic WebGL hero** — a depth-map shader drives a 4s pull-back intro, cursor-reactive 3D parallax, subtle chromatic aberration, barrel-lens curve, a drifting light-leak, and film grain.
- **Name treatment** — Archivo Black (embedded), the letter **A** carries a star built into its counter, revealed with a left-to-right shutter-blur (Wong-Kar-wai style) motion.
- **Seamless gallery** — full-bleed masonry of her work with a fullscreen lightbox (arrow-key nav, shutter transition).
- **Craft** — smooth inertia scroll, custom cursor, scroll-progress bar; degrades gracefully on touch, no-WebGL, and `prefers-reduced-motion`.

## Project layout

```
index.html            # the complete, self-contained site (open this)
src/
  portfolio_tpl.html  # HTML/CSS/JS template with __PLACEHOLDER__ tokens
  build.py            # injects the data assets into the template -> index.html
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

Regenerates `index.html` from the template and `src/data/`.

> Placeholder credits, client names, and the contact email are stand-ins to be replaced with real details.
