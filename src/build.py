#!/usr/bin/env python3
"""Rebuild dist/ (every variant + comparison menu) from src/variants/ + src/data/.

The variant named MAIN is also promoted to the repo-root index.html so the
"just open index.html" promise in the README keeps working.
"""
import json, re, pathlib

d = pathlib.Path(__file__).parent
root = d.parent
MAIN = "01-cinematic.html"

imgs = json.load(open(d / "data/imgdata.json"))
lean = {k: {"uri": v["uri"], "w": v["w"], "h": v["h"]} for k, v in imgs.items()}
dj = json.load(open(d / "data/depthlayers.json"))
depth = {"fx": dj["fx"], "fy": dj["fy"], "depthmap": dj["depthmap"]}
font = (d / "data/font_b64.txt").read_text().strip()
ag = json.load(open(d / "data/aglyph.json"))

FILL = {
    "__IMGDATA__": json.dumps(lean),
    "__DEPTH__": json.dumps(depth),
    "__FONT__": font,
    "__AGLYPH_OUTER__": ag["outer_d"],
    "__AGLYPH_STAR__": ag["star_d"],
}

def build(tpl: str, name: str) -> str:
    out = tpl
    for k, v in FILL.items():
        out = out.replace(k, v)
    assert not re.findall(r"__[A-Z_]+__", out), f"unfilled placeholder in {name}"
    return out

def menu(names: list) -> str:
    cards = []
    for n in names:
        stem = n.rsplit(".", 1)[0]
        num, _, label = stem.partition("-")
        cards.append(f'''
    <a class="card" href="{n}">
      <span class="shot"><iframe src="{n}" loading="lazy" tabindex="-1"></iframe></span>
      <span class="cap"><em>{num}</em> {label.replace("-", " ").upper()}{" <b>&#10022; MAIN</b>" if n == MAIN else ""}</span>
    </a>''')
    return f'''<title>Yulez — design variants</title>
<style>
  @font-face{{font-family:"Blocky";src:url({font}) format("woff2")}}
  body{{margin:0;background:#0b0b0e;color:#f5efe6;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
    min-height:100svh;padding:clamp(20px,4vw,60px)}}
  h1{{font-family:"Blocky","Arial Black",sans-serif;font-weight:400;text-transform:uppercase;
    font-size:clamp(1.6rem,4vw,3rem);margin:0 0 6px;letter-spacing:.01em}}
  h1 i{{color:#ff2116;font-style:normal}}
  p{{color:rgba(245,239,230,.55);margin:0 0 34px;font-size:.85rem;letter-spacing:.06em}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:26px}}
  .card{{display:block;text-decoration:none;color:inherit;border:1px solid rgba(240,232,220,.14);
    background:#101014;transition:border-color .25s,transform .25s}}
  .card:hover{{border-color:rgba(255,33,22,.7);transform:translateY(-3px)}}
  .shot{{display:block;position:relative;aspect-ratio:16/10;overflow:hidden;pointer-events:none}}
  .shot iframe{{position:absolute;top:0;left:0;width:1280px;height:800px;border:0;
    transform-origin:0 0;transform:scale(0.3)}}
  .cap{{display:flex;align-items:center;gap:10px;padding:12px 14px;font-family:"Blocky","Arial Black",sans-serif;
    text-transform:uppercase;font-size:.95rem;letter-spacing:.04em}}
  .cap em{{font-style:normal;color:#ff2116}}
  .cap b{{margin-left:auto;font-weight:400;font-size:.6rem;letter-spacing:.2em;color:rgba(245,239,230,.5)}}
</style>
<h1>Yulez <i>&#10022;</i> variants</h1>
<p>{len(names)} design direction{"s" if len(names) != 1 else ""} in the room — click a card to open it full-bleed.</p>
<div class="grid">{"".join(cards)}
</div>
<script>
  // scale each iframe preview to its card width (1280px virtual viewport)
  function fit(){{document.querySelectorAll(".shot").forEach(function(s){{
    s.querySelector("iframe").style.transform="scale("+(s.clientWidth/1280)+")";}});}}
  addEventListener("resize",fit);fit();
</script>
'''

dist = root / "dist"
dist.mkdir(exist_ok=True)
variants = sorted((d / "variants").glob("*.html"))
assert variants, "no variants found in src/variants/"

names = []
for v in variants:
    out = build(v.read_text(), v.name)
    (dist / v.name).write_text(out)
    names.append(v.name)
    if v.name == MAIN:
        (root / "index.html").write_text(out)
    note = "  -> promoted to index.html" if v.name == MAIN else ""
    print(f"built dist/{v.name}  {len(out)/1024/1024:.2f} MB{note}")

(dist / "index.html").write_text(menu(names))
print(f"built dist/index.html (menu of {len(names)})")
