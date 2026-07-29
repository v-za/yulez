#!/usr/bin/env python3
"""Rebuild dist/ from src/variants/ + src/pages/ + src/data/.

MAIN is copied to the repo-root index.html too, so the "just open
index.html" promise in the README keeps working.

Asset pipeline
--------------
Display images (gallery grids, lightboxes) are emitted as real files under
dist/assets/img/ — original JPEG plus responsive WebP renditions — and pages
reference them via the __IMGFILES__ manifest, so page HTML stays small and
`loading="lazy"` actually defers work.

Anything WebGL samples (the hero texture, the reel atlas sources, cover
photos + depth maps) STAYS inline as data: URIs on purpose: file:// images
taint canvases, and texImage2D from a tainted source throws. data: URIs are
same-origin everywhere. Those inline copies are recompressed to texture-
appropriate sizes (hero keeps full fidelity) when Pillow is available.

Runs on plain python3; with Pillow (e.g. the project venv) it additionally
emits WebP renditions and shrinks the inline GL payload. Emission is
incremental — unchanged sources are skipped via a content-hash stamp.
"""
import base64, hashlib, io, json, re, pathlib, shutil, subprocess

d = pathlib.Path(__file__).parent
root = d.parent
MAIN = "index.html"

imgdata = json.load(open(d / "data/imgdata.json"))
imgs = imgdata["images"]
HERO_KEY = imgdata["_hero"]
dj = json.load(open(d / "data/depthlayers.json"))
depth = {"fx": dj["fx"], "fy": dj["fy"], "depthmap": dj["depthmap"]}
font = (d / "data/font_b64.txt").read_text().strip()
ag = json.load(open(d / "data/aglyph.json"))
font_anton = (d / "data/font_anton_b64.txt").read_text().strip()
ag_anton = json.load(open(d / "data/aglyph_anton.json"))
covers = json.load(open(d / "data/covers.json"))

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

# macOS ships sips, and cwebp comes with webp — together they cover everything
# Pillow does here, so a machine without Pillow still gets responsive images.
CWEBP = shutil.which("cwebp")
SIPS = shutil.which("sips")
HAVE_CLI = bool(CWEBP and SIPS)

def _run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

dist = root / "dist"
ASSETS = dist / "assets" / "img"
ASSETS.mkdir(parents=True, exist_ok=True)
WIDTHS = (320, 480, 640, 960, 1600)   # 320/640 exist for phone-sized cells at 1x/2x
GL_MAX, GL_Q = 1280, 72

stamp_path = dist / "assets" / ".stamp.json"
try:
    stamp = json.loads(stamp_path.read_text())
except Exception:
    stamp = {}

files = {}    # __IMGFILES__: display manifest (src / srcset / w / h)
gl_lean = {}  # __IMGDATA__: inline GL payload
asset_bytes = 0
for k, v in imgs.items():
    raw = base64.b64decode(v["uri"].split(",", 1)[1])
    h = hashlib.sha1(raw).hexdigest()[:12]
    changed = stamp.get(k) != h
    jpg = ASSETS / f"{k}.jpg"
    if changed or not jpg.exists():
        jpg.write_bytes(raw)
    entry = {"src": f"assets/img/{k}.jpg", "w": v["w"], "h": v["h"]}
    if HAVE_PIL:
        im = Image.open(io.BytesIO(raw)); im.load()
        if im.mode != "RGB":
            im = im.convert("RGB")
        srcset = []
        for w in WIDTHS:
            rw = min(w, im.width)
            wp = ASSETS / f"{k}_{w}.webp"
            if changed or not wp.exists():
                r = im.copy(); r.thumbnail((w, 10 ** 6))
                r.save(wp, "WEBP", quality=82, method=4)
            srcset.append(f"assets/img/{k}_{w}.webp {rw}w")
            if rw >= im.width:
                break
        entry["srcset"] = ", ".join(srcset)
        if k == HERO_KEY:
            gl_lean[k] = {"uri": v["uri"], "w": v["w"], "h": v["h"]}
        else:
            g = im.copy(); g.thumbnail((GL_MAX, 10 ** 6))
            buf = io.BytesIO(); g.save(buf, "JPEG", quality=GL_Q, optimize=True)
            gl_lean[k] = {"uri": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(),
                          "w": g.width, "h": g.height}
    elif HAVE_CLI:
        srcset = []
        for w in WIDTHS:
            rw = min(w, v["w"])
            wp = ASSETS / f"{k}_{w}.webp"
            if changed or not wp.exists():
                _run([CWEBP, "-quiet", "-q", "82", "-resize", str(rw), "0",
                      str(jpg), "-o", str(wp)])
            srcset.append(f"assets/img/{k}_{w}.webp {rw}w")
            if rw >= v["w"]:
                break
        entry["srcset"] = ", ".join(srcset)
        if k == HERO_KEY:
            gl_lean[k] = {"uri": v["uri"], "w": v["w"], "h": v["h"]}
        elif v["w"] <= GL_MAX:
            # already texture-sized — re-encoding through sips only inflates it
            gl_lean[k] = {"uri": v["uri"], "w": v["w"], "h": v["h"]}
        else:
            gw = GL_MAX
            gh = max(1, round(v["h"] * gw / v["w"]))
            tmp = ASSETS / f".gl_{k}.jpg"
            if changed or not tmp.exists():
                _run([SIPS, "-Z", str(GL_MAX), "--setProperty", "format", "jpeg",
                      "--setProperty", "formatOptions", str(GL_Q), str(jpg), "--out", str(tmp)])
            gl_lean[k] = {"uri": "data:image/jpeg;base64," + base64.b64encode(tmp.read_bytes()).decode(),
                          "w": gw, "h": gh}
    else:
        gl_lean[k] = {"uri": v["uri"], "w": v["w"], "h": v["h"]}
    files[k] = entry
    stamp[k] = h
    asset_bytes += jpg.stat().st_size
stamp_path.write_text(json.dumps(stamp))

# social share card: hero photo, center-crop 1200x630
if HAVE_PIL:
    og_path = dist / "assets" / "og.jpg"
    if not og_path.exists():
        raw = base64.b64decode(imgs[HERO_KEY]["uri"].split(",", 1)[1])
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        tw, th = 1200, 630
        s = max(tw / im.width, th / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)))
        x, y = (im.width - tw) // 2, (im.height - th) // 2
        im.crop((x, y, x + tw, y + th)).save(og_path, "JPEG", quality=84, optimize=True)
        print("assets: og.jpg (1200x630 share card)")
print(f"assets: {len(imgs)} images -> dist/assets/img "
      f"({asset_bytes/1024/1024:.1f} MB jpg"
      f"{' + webp (Pillow)' if HAVE_PIL else ' + webp (cwebp/sips)' if HAVE_CLI else ', no resizer: webp skipped'})")

FILL = {
    "__IMGDATA__": json.dumps(gl_lean),
    "__IMGFILES__": json.dumps(files),
    "__DEPTH__": json.dumps(depth),
    "__FONT_ANTON__": font_anton,
    "__FONT__": font,
    "__AGLYPH_OUTER_ANTON__": ag_anton["outer_d"],
    "__AGLYPH_STAR_ANTON__": ag_anton["star_d"],
    "__AGLYPH_OUTER__": ag["outer_d"],
    "__AGLYPH_STAR__": ag["star_d"],
    "__HERO__": HERO_KEY,
    "__COVERS__": json.dumps(covers),
}

def build(tpl: str, name: str) -> str:
    out = tpl
    for k, v in FILL.items():
        out = out.replace(k, v)
    assert not re.findall(r"__[A-Z_]+__", out), f"unfilled placeholder in {name}"
    return out

dist = root / "dist"
dist.mkdir(exist_ok=True)
variants = sorted((d / "variants").glob("*.html"))
assert variants, "no variants found in src/variants/"

for v in variants:
    out = build(v.read_text(), v.name)
    (dist / v.name).write_text(out)
    if v.name == MAIN:
        # the root copy lives one level above dist/ — repoint asset urls
        (root / "index.html").write_text(out.replace('assets/img/', 'dist/assets/img/'))
    note = "  -> also repo-root index.html" if v.name == MAIN else ""
    print(f"built dist/{v.name}  {len(out)/1024/1024:.2f} MB{note}")

# standalone pages (galleries, about) — built with the same fill
pages_dir = d / "pages"
if pages_dir.is_dir():
    for p in sorted(pages_dir.glob("*.html")):
        out = build(p.read_text(), p.name)
        (dist / p.name).write_text(out)
        print(f"built dist/{p.name}  {len(out)/1024/1024:.2f} MB  (page)")
