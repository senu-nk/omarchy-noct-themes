"""Render every composition small and tile them into one contact sheet."""
import sys
from PIL import Image
import render
render.set_size(3840 // 6, 2160 // 6)
import compose
from palette import THEMES

tiles = [[render.finish(fn(t.colors(), compose.GEOMETRY[t.key]),
                        seed=compose.GEOMETRY[t.key]["seed"], grain=0.0035)
          for _, fn in compose.COMPOSITIONS] for t in THEMES]

tw, th = tiles[0][0].size
pad = 8
sheet = Image.new("RGB", (4 * tw + 5 * pad, 4 * th + 5 * pad), (26, 26, 28))
for r, row in enumerate(tiles):
    for ci, img in enumerate(row):
        sheet.paste(img, (pad + ci * (tw + pad), pad + r * (th + pad)))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "sheet.png")
print("rows:", ", ".join(t.name for t in THEMES))
print("cols:", ", ".join(n for n, _ in compose.COMPOSITIONS))
