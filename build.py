"""Render the whole theme family into a staging tree."""
import sys, time, pathlib
import render, compose, preview
from palette import THEMES

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "staged")

for t in THEMES:
    c = t.colors()
    g = compose.GEOMETRY[t.key]
    d = OUT / t.slug
    (d / "backgrounds").mkdir(parents=True, exist_ok=True)

    (d / "colors.toml").write_text(t.toml())
    (d / "icons.theme").write_text(t.icons + "\n")

    render.set_size(3840, 2160)
    for name, fn in compose.COMPOSITIONS:
        p = d / "backgrounds" / f"{name}.jpg"
        t0 = time.time()
        render.finish(fn(c, g), seed=g["seed"], grain=0.0035, path=p, quality=96)
        print(f"  {t.slug:9s} {name:9s} {p.stat().st_size/1e6:5.2f} MB  {time.time()-t0:4.1f}s")

    pv = d / "preview.png"
    preview.build(t).save(pv, optimize=True)
    print(f"  {t.slug:9s} {'preview':9s} {pv.stat().st_size/1e6:5.2f} MB")
