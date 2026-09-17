"""Minimalist 4K wallpaper renderer for the Umbra/Cinder/Halcyon/Nimbus family.

Everything is composited in LINEAR light and only encoded to sRGB at the very
end, then dithered with triangular noise. Near-black gradients across 3840x2160
band horribly otherwise -- especially on a large TV panel.
"""
import numpy as np
from PIL import Image

W, H = 3840, 2160


def set_size(w, h):
    """Render smaller while iterating on a composition, full 4K for the real run."""
    global W, H
    W, H = w, h


def size():
    return W, H


def aspect():
    return W / H


# ------------------------------------------------------------------ colour

def srgb_decode(a):
    a = np.asarray(a, np.float32)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def srgb_encode(a):
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def lin(hx):
    """'#rrggbb' -> linear-light float32 triple."""
    hx = hx.lstrip("#")
    return srgb_decode(np.array([int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32))


# ------------------------------------------------------------------ fields

def coords(w=None, h=None):
    """Normalised coords; x in [0,1], y in [0,1]."""
    w, h = w or W, h or H
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    return x, y


def value_noise(w, h, cells, octaves=4, seed=0, persistence=0.5):
    """Smooth fractal noise in [0,1], built by bicubic-upscaling random grids."""
    rng = np.random.default_rng(seed)
    total = np.zeros((h, w), np.float32)
    amp, norm, c = 1.0, 0.0, cells
    for _ in range(octaves):
        g = rng.random((max(2, int(c)) + 1, max(2, int(c)) + 1)).astype(np.float32)
        layer = np.asarray(
            Image.fromarray(g * 255).resize((w, h), Image.BICUBIC), np.float32) / 255
        total += layer * amp
        norm += amp
        amp *= persistence
        c *= 2.0
    total /= norm
    return np.clip(total, 0, 1)


def bloom(cx, cy, radius, falloff=2.2, w=None, h=None):
    """Soft radial light, 1.0 at the centre decaying to 0. Aspect-corrected."""
    w, h = w or W, h or H
    x, y = coords(w, h)
    dx = (x - cx) * (w / h)
    dy = (y - cy)
    d = np.sqrt(dx * dx + dy * dy) / radius
    return np.exp(-np.power(np.clip(d, 0, 12), falloff)).astype(np.float32)


def ring(cx, cy, radius, width, w=None, h=None, softness=1.0):
    """Antialiased hairline circle as a 0..1 mask."""
    w, h = w or W, h or H
    x, y = coords(w, h)
    dx = (x - cx) * (w / h)
    dy = (y - cy)
    d = np.abs(np.sqrt(dx * dx + dy * dy) - radius)
    # width is in normalised-height units; one pixel = 1/h
    edge = softness / h
    return np.clip(1.0 - (d - width * 0.5) / edge, 0.0, 1.0).astype(np.float32)


def vgrad(stops, w=None, h=None):
    """Vertical gradient from [(pos, linear_rgb), ...] with smoothstep easing."""
    w, h = w or W, h or H
    _, y = coords(w, h)
    y = y[:, 0]
    out = np.zeros((h, 3), np.float32)
    stops = sorted(stops, key=lambda s: s[0])
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        m = (y >= p0) & (y <= p1)
        if not m.any():
            continue
        t = (y[m] - p0) / max(p1 - p0, 1e-6)
        t = t * t * (3 - 2 * t)                    # smoothstep
        out[m] = c0[None, :] * (1 - t[:, None]) + c1[None, :] * t[:, None]
    out[y < stops[0][0]] = stops[0][1]
    out[y > stops[-1][0]] = stops[-1][1]
    return np.repeat(out[:, None, :], w, axis=1)


# ------------------------------------------------------------------ output

def finish(rgb_linear, seed=0, grain=0.0035, path=None, quality=96):
    """Linear -> sRGB, add film grain + TPDF dither, save."""
    rng = np.random.default_rng(seed + 9901)
    srgb = srgb_encode(rgb_linear)

    if grain > 0:
        # Luminance-linked grain: heavier in the mids, near-absent in pure black,
        # which is how real film behaves and what stops the gradient reading CGI.
        lum = srgb.mean(axis=2, keepdims=True)
        weight = np.sqrt(np.clip(lum, 0, 1) + 0.06)
        srgb = srgb + rng.normal(0, grain, srgb.shape).astype(np.float32) * weight

    # Triangular-PDF dither at +-1 LSB: the actual anti-banding step.
    tpdf = (rng.random(srgb.shape, dtype=np.float32)
            - rng.random(srgb.shape, dtype=np.float32)) / 255.0
    srgb = np.clip(srgb + tpdf, 0, 1)

    img = Image.fromarray((srgb * 255 + 0.5).astype(np.uint8), "RGB")
    if path:
        if str(path).endswith((".jpg", ".jpeg")):
            img.save(path, quality=quality, subsampling=0, optimize=True,
                     progressive=True)
        else:
            img.save(path, optimize=True)
    return img
