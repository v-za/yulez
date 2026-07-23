#!/usr/bin/env python3
"""Rebuild index.html from the template + embedded data assets."""
import json, re, pathlib
d = pathlib.Path(__file__).parent
tpl = (d / "portfolio_tpl.html").read_text()
imgs = json.load(open(d / "data/imgdata.json"))
lean = {k: {"uri": v["uri"], "w": v["w"], "h": v["h"]} for k, v in imgs.items()}
dj = json.load(open(d / "data/depthlayers.json"))
depth = {"fx": dj["fx"], "fy": dj["fy"], "depthmap": dj["depthmap"]}
font = (d / "data/font_b64.txt").read_text().strip()
ag = json.load(open(d / "data/aglyph.json"))
out = (tpl.replace("__IMGDATA__", json.dumps(lean))
          .replace("__DEPTH__", json.dumps(depth))
          .replace("__FONT__", font)
          .replace("__AGLYPH_OUTER__", ag["outer_d"])
          .replace("__AGLYPH_STAR__", ag["star_d"]))
assert not re.findall(r"__[A-Z_]+__", out), "unfilled placeholder remains"
(d.parent / "index.html").write_text(out)
print("built index.html", round(len(out) / 1024 / 1024, 2), "MB")
