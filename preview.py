"""Theme preview card for the Omarchy theme switcher.

A staged desktop: the theme's own wallpaper, a bar, a terminal showing the
syntax palette in use, and a swatch panel. 1800x1012, matching stock themes.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import render
import compose

PW, PH = 1800, 1012
FONT = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf"
FONT_B = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"


def rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def panel(img, box, fill, radius=14, border=None, shadow=42, alpha=252):
    """Rounded card with a soft drop shadow, composited onto img."""
    x0, y0, x1, y1 = box
    if shadow:
        pad = shadow * 2
        sh = Image.new("L", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), 0)
        ImageDraw.Draw(sh).rounded_rectangle(
            (pad, pad + 8, pad + (x1 - x0), pad + 8 + (y1 - y0)),
            radius=radius, fill=190)
        sh = sh.filter(ImageFilter.GaussianBlur(shadow * 0.55))
        img.paste(Image.new("RGB", sh.size, (0, 0, 0)), (x0 - pad, y0 - pad), sh)

    card = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=radius,
                        fill=fill + (alpha,),
                        outline=(border + (255,)) if border else None, width=1)
    img.paste(card, (x0, y0), card)


def build(theme):
    c = theme.colors()
    g = compose.GEOMETRY[theme.key]

    # --- wallpaper ------------------------------------------------------
    render.set_size(PW, PH)
    img = render.finish(compose.BY_NAME[theme.hero](c, g),
                        seed=g["seed"], grain=0.0030).convert("RGB")
    render.set_size(3840, 2160)

    FG = rgb(c["foreground"])
    DIM = rgb(c["dark_foreground"])
    LIGHT = rgb(c["light_foreground"])
    BRIGHT = rgb(c["bright_foreground"])
    ACC = rgb(c["accent"])
    BG = rgb(c["background"])
    DBG = rgb(c["dark_background"])
    LBG = rgb(c["lighter_background"])
    MUT = rgb(c["muted"])

    f14 = ImageFont.truetype(FONT, 14)
    f15 = ImageFont.truetype(FONT, 15)
    f17 = ImageFont.truetype(FONT, 17)
    f17b = ImageFont.truetype(FONT_B, 17)
    f22b = ImageFont.truetype(FONT_B, 22)
    f30b = ImageFont.truetype(FONT_B, 30)

    # --- top bar --------------------------------------------------------
    bar = Image.new("RGBA", (PW, 38), DBG + (232,))
    d = ImageDraw.Draw(bar)
    for i, lbl in enumerate(["1", "2", "3", "4"]):
        x = 26 + i * 30
        d.text((x, 11), lbl, font=f15, fill=ACC if i == 0 else DIM)
    d.text((PW // 2 - 62, 11), "Wed 17 Sep  14:26", font=f15, fill=LIGHT)
    d.text((PW - 268, 11), "cpu 12%", font=f15, fill=DIM)
    d.text((PW - 168, 11), "vol 62", font=f15, fill=DIM)
    d.text((PW - 78, 11), "84%", font=f15, fill=mix(DIM, ACC, 0.5))
    img.paste(bar, (0, 0), bar)

    # --- terminal -------------------------------------------------------
    tx0, ty0, tx1, ty1 = 86, 118, 1036, 762
    panel(img, (tx0, ty0, tx1, ty1), BG, radius=14, border=mix(BG, ACC, 0.34))
    d = ImageDraw.Draw(img)
    d.line((tx0 + 1, ty0 + 44, tx1 - 2, ty0 + 44), fill=mix(BG, MUT, 0.7))
    d.text((tx0 + 22, ty0 + 15), "senuka@omarchy: ~/.config/hypr", font=f15, fill=DIM)
    d.text((tx1 - 150, ty0 + 15), theme.slug, font=f15, fill=mix(DIM, ACC, 0.55))

    # syntax-coloured source, the honest test of any palette
    L = [
        [("  1 ", DIM), ("local", rgb(c["magenta"])), (" ", FG),
         ("o", rgb(c["blue"])), (" = ", FG), ("require", rgb(c["cyan"])),
         ("(", MUT), ('"omarchy"', rgb(c["green"])), (")", MUT)],
        [("  2 ", DIM)],
        [("  3 ", DIM), ("-- hairline borders, no chrome", rgb(c["dark_foreground"]))],
        [("  4 ", DIM), ("o", rgb(c["blue"])), (".", MUT),
         ("looknfeel", rgb(c["yellow"])), ("({", MUT)],
        [("  5 ", DIM), ("  gaps_in", FG), (" = ", MUT), ("4", rgb(c["orange"])), (",", MUT)],
        [("  6 ", DIM), ("  gaps_out", FG), (" = ", MUT), ("10", rgb(c["orange"])), (",", MUT)],
        [("  7 ", DIM), ("  border_size", FG), (" = ", MUT),
         ("1", rgb(c["orange"])), (",", MUT)],
        [("  8 ", DIM), ("  rounding", FG), (" = ", MUT),
         ("10", rgb(c["orange"])), (",", MUT)],
        [("  9 ", DIM), ("})", MUT)],
        [(" 10 ", DIM)],
        [(" 11 ", DIM), ("for", rgb(c["magenta"])), (" _, ", FG),
         ("w", rgb(c["blue"])), (" in ", rgb(c["magenta"])),
         ("ipairs", rgb(c["cyan"])), ("(", MUT), ("windows", rgb(c["blue"])),
         (")", MUT), (" do", rgb(c["magenta"]))],
        [(" 12 ", DIM), ("  ", FG), ("w", rgb(c["blue"])), (":", MUT),
         ("dim", rgb(c["yellow"])), ("(", MUT), ("0.92", rgb(c["orange"])), (")", MUT)],
        [(" 13 ", DIM), ("end", rgb(c["magenta"]))],
        [(" 14 ", DIM)],
        [(" 15 ", DIM), ("o", rgb(c["blue"])), (".", MUT),
         ("bind", rgb(c["yellow"])), ("(", MUT), ('"SUPER"', rgb(c["green"])),
         (", ", MUT), ('"return"', rgb(c["green"])), (", ", MUT),
         ("term", rgb(c["cyan"])), (")", MUT)],
        [(" 16 ", DIM), ("assert", rgb(c["red"])), ("(", MUT),
         ("o", rgb(c["blue"])), (".", MUT), ("ok", rgb(c["yellow"])),
         ("(), ", MUT), ('"theme failed"', rgb(c["green"])), (")", MUT)],
    ]
    y = ty0 + 70
    for line in L:
        x = tx0 + 22
        for txt, col in line:
            d.text((x, y), txt, font=f17, fill=col)
            x += d.textlength(txt, font=f17)
        y += 27

    # status line + prompt
    sy = ty1 - 86
    d.rectangle((tx0 + 1, sy, tx1 - 2, sy + 26), fill=mix(BG, LBG, 1.0))
    d.rectangle((tx0 + 1, sy, tx0 + 82, sy + 26), fill=ACC)
    d.text((tx0 + 18, sy + 5), "NORMAL", font=f15, fill=rgb(c["darker_background"]))
    d.text((tx0 + 98, sy + 5), "hypr/looknfeel.lua", font=f15, fill=LIGHT)
    d.text((tx1 - 112, sy + 5), "11:4", font=f15, fill=DIM)

    cmd = "omarchy theme set " + theme.slug
    x = tx0 + 22
    for txt, col, fnt in [("~/.config", ACC, f17b), ("  main", rgb(c["blue"]), f17),
                          ("  \u276f ", rgb(c["magenta"]), f17b), (cmd, FG, f17)]:
        d.text((x, sy + 44), txt, font=fnt, fill=col)
        x += d.textlength(txt, font=fnt)
    d.rectangle((x + 3, sy + 45, x + 13, sy + 66), fill=BRIGHT)

    # --- palette panel --------------------------------------------------
    px0, py0, px1, py1 = 1098, 268, 1714, 798
    panel(img, (px0, py0, px1, py1), DBG, radius=16, border=mix(DBG, MUT, 0.9))
    d = ImageDraw.Draw(img)
    d.text((px0 + 34, py0 + 34), theme.name, font=f30b, fill=BRIGHT)
    d.text((px0 + 34, py0 + 76), theme.tagline, font=f15, fill=DIM)
    d.line((px0 + 34, py0 + 112, px1 - 34, py0 + 112), fill=mix(DBG, MUT, 0.8))

    rows = [
        ["red", "orange", "yellow", "green"],
        ["cyan", "blue", "magenta", "accent"],
    ]
    sw, sh, gap = 130, 88, 18
    for r, row in enumerate(rows):
        for q, key in enumerate(row):
            x = px0 + 34 + q * (sw + gap)
            yy = py0 + 140 + r * (sh + 46)
            d.rounded_rectangle((x, yy, x + sw, yy + sh), radius=9, fill=rgb(c[key]))
            d.text((x + 2, yy + sh + 8), c[key], font=f14, fill=DIM)

    # surface ladder as one continuous strip
    yy = py0 + 140 + 2 * (sh + 46) + 16
    d.text((px0 + 34, yy), "SURFACES", font=f14, fill=mix(DIM, MUT, 0.4))
    yy += 26
    ladder = ["darker_background", "dark_background", "background",
              "lighter_background", "selection", "muted"]
    step = (px1 - px0 - 68) / len(ladder)
    for i, key in enumerate(ladder):
        x = px0 + 34 + i * step
        d.rectangle((x, yy, x + step, yy + 46), fill=rgb(c[key]))
    d.rounded_rectangle((px0 + 34, yy, px1 - 34, yy + 46), radius=6,
                        outline=mix(DBG, MUT, 0.9), width=1)

    # --- window border accent on the focused window ---------------------
    d.rounded_rectangle((tx0, ty0, tx1 - 1, ty1 - 1), radius=14,
                        outline=ACC, width=2)

    return img
