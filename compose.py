"""Four wallpaper compositions for the Noct family.

Direction: bold graphic forms that fill the frame -- large, high-contrast, nothing
floating in the middle of a black field.

Two rules learned the hard way:
  * Big forms are LIT, not painted. Every large area carries a gradient across it.
    Flat saturated planes read as poster paint and fight the windows on top.
  * Calm comes from the gradient falling off, never from leaving a rectangle of
    black. A hard vertical seam where a composition simply stops looks unfinished.

Each composition is built from signed-distance fields and alpha-composited in
LINEAR light; render.finish() does the sRGB encode, grain and dither.
"""
import numpy as np
from PIL import Image
import render
from render import lin, coords, value_noise, finish

AS = 16 / 9          # frame width in height units


# ------------------------------------------------------------------ space

def frame():
    """X in [0, AS], Y in [0, 1]. One unit = one frame height."""
    x, y = coords()
    return x * render.aspect(), y


def fill(sd, softpx=2.0):
    return np.clip(0.5 - sd * render.H / softpx, 0.0, 1.0).astype(np.float32)


def stroke(sd, width_px, softpx=2.0):
    return fill(np.abs(sd) - (width_px / render.H) * 0.5, softpx)


def sd_circle(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def sd_half(X, Y, px, py, angle):
    """Negative on the side the normal points away from."""
    nx, ny = np.cos(angle), np.sin(angle)
    return (X - px) * nx + (Y - py) * ny


def sd_band(X, Y, px, py, angle, halfwidth):
    return np.abs(sd_half(X, Y, px, py, angle)) - halfwidth


# ------------------------------------------------------------------ tone

def tone(hexcolor, level):
    """Linear RGB of this hue, rescaled so its sRGB luminance is `level` (0..1).

    Lets a composition be specified in the values you actually want to see,
    independent of how light or saturated a given theme's accent happens to be.
    """
    a = lin(hexcolor)
    y = float(0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2])
    target = float(render.srgb_decode(np.float32(level)))
    return (a * (target / max(y, 1e-5))).astype(np.float32)


def mix(c0, c1, t):
    """Blend two linear colours by a scalar field t, giving an HxWx3 field."""
    c0 = np.asarray(c0, np.float32)
    c1 = np.asarray(c1, np.float32)
    return (c0[None, None, :] * (1 - t[..., None])
            + c1[None, None, :] * t[..., None]).astype(np.float32)


def paint(base, cov, color):
    """Composite `color` (a triple or an HxWx3 field) over base by coverage."""
    a = cov[..., None] if cov.ndim == 2 else cov
    col = color if getattr(color, "ndim", 0) == 3 else \
        np.asarray(color, np.float32)[None, None, :]
    return (base * (1 - a) + col * a).astype(np.float32)


def ramp(px, py, angle, length, ease=True):
    """0..1 gradient field running along `angle`, starting at (px, py)."""
    X, Y = frame()
    nx, ny = np.cos(angle), np.sin(angle)
    t = np.clip(((X - px) * nx + (Y - py) * ny) / length, 0, 1)
    if ease:
        t = t * t * (3 - 2 * t)
    return t.astype(np.float32)


def radial(cx, cy, r, falloff=1.8):
    X, Y = frame()
    d = np.hypot(X - cx, Y - cy) / r
    return np.exp(-np.power(np.clip(d, 0, 12), falloff)).astype(np.float32)


def mottle(seed, cells=2, octaves=4, lo=0.90, hi=1.10):
    t = value_noise(render.W // 6, render.H // 6, cells=cells, octaves=octaves, seed=seed)
    t = np.asarray(Image.fromarray(t * 255)
                   .resize((render.W, render.H), Image.BICUBIC), np.float32) / 255.0
    return (lo + (hi - lo) * t).astype(np.float32)


def vignette(strength=0.15, power=2.0):
    x, y = coords()
    d = np.clip(np.hypot((x - 0.5) * 2, (y - 0.5) * 2) / 1.414, 0, 1)
    return (1.0 - strength * np.power(d, power)).astype(np.float32)


def arc_weight(cx, cy, angle, spread):
    """1 along a chosen bearing from a centre, falling to 0 `spread` radians away.

    Used to light only part of a rim, so a circle reads as lit from a direction
    instead of outlined like a sticker.
    """
    X, Y = frame()
    a = np.arctan2(Y - cy, X - cx)
    d = np.abs(((a - angle + np.pi) % (2 * np.pi)) - np.pi) / spread
    return np.clip(1.0 - d * d, 0, 1).astype(np.float32)


# ------------------------------------------------------------------ geometry

GEOMETRY = {
    "umbra": dict(
        seed=11,
        disc=(0.27 * AS, 0.71, 0.66), disc_light=-0.75, field_dir=-2.35,
        sweep=(0.55 * AS, 0.50, 0.42, 0.150),
        terrace=dict(hz=0.615, sun=(0.62 * AS, 0.84, 0.500), n=6),
        split=dict(edge=(0.52 * AS, 0.50, 1.19), circ=(0.60 * AS, 0.41, 0.455)),
    ),
    "cinder": dict(
        seed=23,
        disc=(0.74 * AS, 0.30, 0.61), disc_light=2.30, field_dir=0.72,
        sweep=(0.45 * AS, 0.52, -0.38, 0.175),
        terrace=dict(hz=0.545, sun=(0.34 * AS, 0.74, 0.445), n=5),
        split=dict(edge=(0.46 * AS, 0.48, -1.31), circ=(0.38 * AS, 0.60, 0.410)),
    ),
    "halcyon": dict(
        seed=37,
        disc=(0.31 * AS, 0.26, 0.71), disc_light=1.05, field_dir=2.05,
        sweep=(0.50 * AS, 0.46, 0.30, 0.205),
        terrace=dict(hz=0.680, sun=(0.57 * AS, 0.91, 0.560), n=7),
        split=dict(edge=(0.55 * AS, 0.53, 0.94), circ=(0.66 * AS, 0.57, 0.500)),
    ),
    "nimbus": dict(
        seed=53,
        disc=(0.70 * AS, 0.76, 0.58), disc_light=-2.55, field_dir=-0.95,
        sweep=(0.52 * AS, 0.49, -0.48, 0.135),
        terrace=dict(hz=0.470, sun=(0.41 * AS, 0.66, 0.400), n=5),
        split=dict(edge=(0.49 * AS, 0.47, -0.88), circ=(0.41 * AS, 0.38, 0.435)),
    ),
}


# ------------------------------------------------------------------ 1. ECLIPSE

def eclipse(c, g):
    """One enormous body against a lit field, rimmed on the side facing the light."""
    X, Y = frame()
    cx, cy, R = g["disc"]
    seed = g["seed"]

    deep = tone(c["darker_background"], 0.042)
    lit = tone(c["accent"], 0.315)

    field = mix(deep, lit, ramp(0.5 * AS - np.cos(g["field_dir"]) * 1.15,
                                0.5 - np.sin(g["field_dir"]) * 1.15,
                                g["field_dir"], 2.05))
    out = field * mottle(seed, lo=0.89, hi=1.11)[..., None]

    # the body: not flat black -- it picks up a little of the field it sits in
    body = mix(tone(c["darker_background"], 0.034),
               tone(c["accent"], 0.105),
               ramp(cx - np.cos(g["disc_light"]) * R, cy - np.sin(g["disc_light"]) * R,
                    g["disc_light"], R * 2.0))
    sd = sd_circle(X, Y, cx, cy, R)
    out = paint(out, fill(sd, 2.2), body * mottle(seed + 4, lo=0.93, hi=1.07)[..., None])

    # rim, only on the lit side
    w = arc_weight(cx, cy, g["disc_light"], 1.45)
    out = paint(out, stroke(sd, 5.0) * w,
                tone(c["accent"], 0.68) * 0.55 + lin(c["bright_foreground"]) * 0.10)
    out = paint(out, stroke(sd, 26.0, softpx=70.0) * w * 0.35, tone(c["accent"], 0.46))

    return out * vignette(0.15)[..., None]


# ------------------------------------------------------------------ 2. SWEEP

def sweep(c, g):
    """A single wide band of light crossing the frame, bright at one end."""
    X, Y = frame()
    px, py, angle, halfw = g["sweep"]
    seed = g["seed"]
    along = angle + np.pi / 2

    deep = tone(c["darker_background"], 0.040)
    out = mix(deep, tone(c["accent"], 0.105),
              ramp(px - np.cos(along) * 1.2, py - np.sin(along) * 1.2, along, 2.4))
    out = out * mottle(seed, lo=0.89, hi=1.11)[..., None]

    # the band itself, fading along its length
    band = mix(tone(c["accent"], 0.395), tone(c["darker_background"], 0.075),
               ramp(px - np.cos(along) * halfw * 5.0,
                    py - np.sin(along) * halfw * 5.0, along, 2.15))
    sd = sd_band(X, Y, px, py, angle, halfw)
    out = paint(out, fill(sd, 2.4), band * mottle(seed + 6, lo=0.92, hi=1.08)[..., None])

    # a bright edge on the leading side only
    lead = fill(sd_half(X, Y, px, py, angle), 2.4)
    out = paint(out, stroke(sd, 3.4) * lead, tone(c["accent"], 0.66))

    # one narrow echo running parallel, well off to the side
    off = halfw * 3.4
    sd2 = sd_band(X + np.cos(angle) * off, Y + np.sin(angle) * off, px, py, angle,
                  halfw * 0.16)
    out = paint(out, fill(sd2, 2.2) * 0.75, tone(c["accent"], 0.235))

    return out * vignette(0.15)[..., None]


# ------------------------------------------------------------------ 3. TERRACE

def terrace(c, g):
    """A body rising behind full-width strata. Bands span edge to edge -- no seams."""
    X, Y = frame()
    t = g["terrace"]
    hz, (sx, sy, sr), n = t["hz"], t["sun"], t["n"]
    seed = g["seed"]

    deep = tone(c["darker_background"], 0.040)
    sky = mix(tone(c["darker_background"], 0.052), tone(c["accent"], 0.225),
              ramp(0.0, hz - 0.92, np.pi / 2, 0.92))
    out = sky * mottle(seed, lo=0.90, hi=1.10)[..., None]

    # the body, behind everything below the horizon
    disc = mix(tone(c["accent"], 0.455), tone(c["accent"], 0.205),
               ramp(sx, sy - sr, np.pi / 2, sr * 2.0))
    out = paint(out, fill(sd_circle(X, Y, sx, sy, sr), 2.2), disc)
    out = paint(out, stroke(sd_circle(X, Y, sx, sy, sr), 3.0)
                * arc_weight(sx, sy, -np.pi / 2, 1.9), tone(c["accent"], 0.66))

    # strata: full width, uneven heights, each one lit across its own length
    rng = np.random.default_rng(seed)
    weights = np.array([0.34, 0.09, 0.23, 0.06, 0.28, 0.13, 0.19][:n], np.float64)
    rng.shuffle(weights)
    weights /= weights.sum()
    edges = [0.0, *np.cumsum(weights)]
    for i in range(n):
        y0 = hz + (1.0 - hz) * edges[i]
        y1 = hz + (1.0 - hz) * edges[i + 1]
        lvl = 0.055 + 0.175 * (1.0 - i / max(n - 1, 1)) ** 1.5
        dirn = 0.0 if i % 2 == 0 else np.pi
        band = mix(tone(c["accent"], lvl * 0.55), tone(c["accent"], lvl * 1.5),
                   ramp(0.0 if i % 2 == 0 else AS, 0.0, dirn, AS))
        cov = fill(np.maximum(y0 - Y, Y - y1), 2.0)
        out = paint(out, cov, band * mottle(seed + i, lo=0.93, hi=1.07)[..., None])
        if i:
            out = paint(out, stroke(Y - y0, 1.4) * 0.45, tone(c["accent"], 0.34))

    out = paint(out, stroke(Y - hz, 2.4), tone(c["accent"], 0.60))
    return out * vignette(0.15)[..., None]


# ------------------------------------------------------------------ 4. SPLIT

def split(c, g):
    """One hard diagonal, one huge circle straddling it, inverted where they cross."""
    X, Y = frame()
    s = g["split"]
    ex, ey, eang = s["edge"]
    cx, cy, R = s["circ"]
    seed = g["seed"]

    along = eang + np.pi / 2
    dark = mix(tone(c["darker_background"], 0.038), tone(c["accent"], 0.098),
               ramp(ex - np.cos(along) * 1.1, ey - np.sin(along) * 1.1, along, 2.2))
    light = mix(tone(c["accent"], 0.410), tone(c["accent"], 0.205),
                ramp(ex - np.cos(along) * 1.1, ey - np.sin(along) * 1.1, along, 2.2))

    side = fill(sd_half(X, Y, ex, ey, eang), 2.4)          # 1 on the light side
    tex = mottle(seed, lo=0.90, hi=1.10)[..., None]
    base = (dark * (1 - side[..., None]) + light * side[..., None]) * tex
    swap = (light * (1 - side[..., None]) + dark * side[..., None]) * tex

    sd = sd_circle(X, Y, cx, cy, R)
    out = paint(base, fill(sd, 2.4), swap)

    # the circle's outline only where it crosses into the dark side, and a
    # hairline along the diagonal only where it is not covered by the circle
    out = paint(out, stroke(sd, 3.0) * (1 - side) * 0.9, tone(c["accent"], 0.64))
    out = paint(out, stroke(sd_half(X, Y, ex, ey, eang), 2.2) * (1 - fill(sd, 2.4)),
                tone(c["accent"], 0.58))

    return out * vignette(0.15)[..., None]


COMPOSITIONS = [("1-eclipse", eclipse), ("2-sweep", sweep),
                ("3-terrace", terrace), ("4-split", split)]
BY_NAME = dict(COMPOSITIONS)
