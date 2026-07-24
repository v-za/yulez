#!/usr/bin/env python3
"""Rebuild dist/ (every variant + comparison menu) from src/variants/ + src/data/.

The variant named MAIN is also promoted to the repo-root index.html so the
"just open index.html" promise in the README keeps working.

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
import base64, hashlib, io, json, re, pathlib

d = pathlib.Path(__file__).parent
root = d.parent
MAIN = "01-cinematic.html"

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

dist = root / "dist"
ASSETS = dist / "assets" / "img"
ASSETS.mkdir(parents=True, exist_ok=True)
WIDTHS = (480, 960, 1600)
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
      f"({asset_bytes/1024/1024:.1f} MB jpg{' + webp renditions' if HAVE_PIL else ', no Pillow: webp skipped'})")

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

def menu(names: list) -> str:
    tree = json.load(open(d / "decisions.json"))

    cols, edges, filed = [], [], set()
    def walk(dec, depth, from_id, kind=""):
        while len(cols) <= depth:
            cols.append([])
        did = f"d{depth}-{len(cols[depth])}"
        opts_html = []
        for j, o in enumerate(dec.get("options", [])):
            oid = f"{did}-o{j}"
            st = o.get("state", "")
            filed.add(o.get("file", ""))
            shot = (f'<span class="shot"><iframe data-src="{o["file"]}" tabindex="-1"></iframe><i class="hint">hover to preview</i></span>'
                    if o.get("file") else "")
            badge = ' <b>&#10022;</b>' if st == "chosen" else (' <b class="soft">leaning</b>' if st == "leaning" else "")
            opts_html.append(f'''
      <a class="onode {st}" id="{oid}" href="{o.get("file","#")}">{shot}
        <span class="cap">{o["label"].upper()}{badge}</span>
        {f'<span class="note">{o["note"]}</span>' if o.get("note") else ''}</a>''')
            if o.get("next"):
                walk(o["next"], depth + 1, oid, st)
        body = "".join(opts_html) if opts_html else '<div class="empty">prototype coming</div>'
        cols[depth].append(f'''
    <div class="dnode" id="{did}">
      <h2>{dec["decision"]}</h2><span class="q">{dec.get("question","")}</span>
      <div class="opts">{body}</div>
    </div>''')
        if from_id:
            edges.append((from_id, did, kind))
        return did
    walk(tree, 0, None)

    columns = "".join(f'<div class="col">{"".join(c)}</div>' for c in cols)
    unfiled = [n for n in names if n not in filed]
    unfiled_html = ("" if not unfiled else
        '<div class="unfiled"><span>unfiled:</span>' +
        "".join(f'<a href="{n}">{n}</a>' for n in unfiled) + '</div>')
    edge_data = json.dumps([{"a": a, "b": b, "k": k} for a, b, k in edges])
    return f'''<title>Yulez — decision graph</title>
<style>
  @font-face{{font-family:"Blocky";src:url({font}) format("woff2")}}
  body{{margin:0;background:#0b0b0e;color:#f5efe6;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
    min-height:100svh;padding:clamp(20px,3vw,44px)}}
  h1{{font-family:"Blocky","Arial Black",sans-serif;font-weight:400;text-transform:uppercase;
    font-size:clamp(1.6rem,4vw,3rem);margin:0 0 6px;letter-spacing:.01em}}
  h1 i{{color:#ff2116;font-style:normal}}
  .lede{{color:rgba(245,239,230,.55);margin:0 0 30px;font-size:.85rem;letter-spacing:.06em}}

  #graph{{position:relative;display:flex;gap:clamp(48px,6vw,110px);align-items:flex-start;
    overflow-x:auto;padding:10px 4px 30px}}
  #wires{{position:absolute;inset:0;pointer-events:none;overflow:visible}}
  .col{{display:flex;flex-direction:column;gap:34px;min-width:300px;max-width:360px;flex:0 0 auto}}

  .dnode h2{{font-family:"Blocky","Arial Black",sans-serif;font-weight:400;text-transform:uppercase;
    font-size:1.1rem;margin:0;letter-spacing:.03em}}
  .dnode .q{{display:block;color:rgba(245,239,230,.45);font-size:.72rem;letter-spacing:.04em;margin:3px 0 12px}}
  .opts{{display:flex;flex-direction:column;gap:14px}}

  .onode{{display:block;text-decoration:none;color:inherit;border:1px solid rgba(240,232,220,.16);
    background:#101014;transition:border-color .25s,transform .25s;position:relative}}
  .onode:hover{{border-color:rgba(255,33,22,.7);transform:translateY(-2px)}}
  .onode.chosen{{border-color:#ff2116}}
  .onode.leaning{{border-color:rgba(255,33,22,.45);border-style:dashed}}
  .shot{{display:block;position:relative;aspect-ratio:16/10;overflow:hidden;pointer-events:none;background:#0b0b0e}}
  .shot iframe{{position:absolute;top:0;left:0;width:1280px;height:800px;border:0;
    transform-origin:0 0;transform:scale(0.24)}}
  .shot .hint{{position:absolute;inset:0;display:grid;place-items:center;font-style:normal;
    font-family:ui-monospace,Menlo,monospace;font-size:.6rem;letter-spacing:.22em;text-transform:uppercase;
    color:rgba(245,239,230,.35)}}
  .onode.live .hint{{display:none}}
  .cap{{display:flex;align-items:baseline;gap:8px;padding:10px 12px 2px;font-family:"Blocky","Arial Black",sans-serif;
    text-transform:uppercase;font-size:.85rem;letter-spacing:.04em}}
  .cap b{{margin-left:auto;font-weight:400;color:#ff2116;font-size:.9rem}}
  .cap b.soft{{font-family:ui-monospace,Menlo,monospace;font-size:.55rem;letter-spacing:.2em;
    color:rgba(255,33,22,.75)}}
  .note{{display:block;padding:2px 12px 11px;font-size:.68rem;color:rgba(245,239,230,.5);letter-spacing:.02em}}
  .empty{{border:1px dashed rgba(240,232,220,.25);padding:26px 18px;color:rgba(245,239,230,.4);
    font-size:.75rem;letter-spacing:.06em}}
  .unfiled{{margin-top:8px;font-family:ui-monospace,Menlo,monospace;font-size:.65rem;letter-spacing:.1em;
    color:rgba(245,239,230,.45)}}
  .unfiled a{{color:rgba(245,239,230,.7);margin-left:12px}}
</style>
<h1>Yulez <i>&#10022;</i> decision graph</h1>
<p class="lede">Left to right: each choice opens the next. Solid red = chosen &#10022; &middot; dashed red = leaning &middot; click any card to open it full-bleed.</p>
<div id="graph"><svg id="wires"></svg>{columns}</div>
{unfiled_html}
<script>
  var EDGES={edge_data};
  function fit(){{}}
  function wires(){{
    var g=document.getElementById('graph'),svg=document.getElementById('wires');
    var gr=g.getBoundingClientRect(),sx=g.scrollLeft;
    svg.setAttribute('width',g.scrollWidth);svg.setAttribute('height',g.scrollHeight);
    svg.innerHTML=EDGES.map(function(e){{
      var a=document.getElementById(e.a),b=document.getElementById(e.b);
      if(!a||!b)return '';
      var ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();
      var x1=ra.right-gr.left+sx,y1=ra.top+ra.height/2-gr.top;
      var x2=rb.left-gr.left+sx,y2=rb.top+16-gr.top;
      var mx=(x1+x2)/2;
      var hot=e.k==='chosen'||e.k==='leaning';
      return '<path d="M'+x1+' '+y1+' C'+mx+' '+y1+','+mx+' '+y2+','+x2+' '+y2+
        '" fill="none" stroke="'+(hot?'#ff2116':'rgba(240,232,220,.25)')+
        '" stroke-width="'+(hot?2:1.2)+'"'+(e.k==='leaning'?' stroke-dasharray="6 5"':'')+'/>';
    }}).join('');
  }}
  /* live previews only on hover, one at a time — 4 idle 9MB WebGL iframes
     was killing the whole machine */
  var liveNode=null;
  document.querySelectorAll('.onode').forEach(function(n){{
    var f=n.querySelector('iframe'); if(!f)return;
    n.addEventListener('mouseenter',function(){{
      if(liveNode&&liveNode!==n){{var lf=liveNode.querySelector('iframe');
        lf.removeAttribute('src');liveNode.classList.remove('live');}}
      f.src=f.getAttribute('data-src');n.classList.add('live');liveNode=n;
    }});
  }});
  function all(){{fit();wires();}}
  addEventListener('resize',all);
  document.getElementById('graph').addEventListener('scroll',wires);
  all();setTimeout(all,300);setTimeout(all,1200);
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
        # the root copy lives one level above dist/ — repoint asset urls
        (root / "index.html").write_text(out.replace('assets/img/', 'dist/assets/img/'))
    note = "  -> promoted to index.html" if v.name == MAIN else ""
    print(f"built dist/{v.name}  {len(out)/1024/1024:.2f} MB{note}")

# standalone pages (galleries etc.) — built with the same fill, no menu card
pages_dir = d / "pages"
if pages_dir.is_dir():
    for p in sorted(pages_dir.glob("*.html")):
        out = build(p.read_text(), p.name)
        (dist / p.name).write_text(out)
        print(f"built dist/{p.name}  {len(out)/1024/1024:.2f} MB  (page)")

# the menu: dist/index.html unless another session has symlinked index to a
# variant (promoting it to landing page) — then the menu lives at menu.html
menu_path = dist / ("menu.html" if (dist / "index.html").is_symlink() else "index.html")
menu_path.write_text(menu(names))
print(f"built {menu_path.relative_to(root)} (menu of {len(names)})")
