"""OKLCH -> sRGB palette engine for the Noct theme family.

Every theme is generated from the same perceptual ladder (identical L* values for
background/foreground roles across all four) so the four themes feel like one
design system with the hue swapped out.
"""
import math

# ---------------------------------------------------------------- oklab <-> srgb

def _srgb_encode(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def _srgb_decode(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def oklab_to_linear(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def in_gamut(L, C, h):
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    return all(-1e-4 <= v <= 1.0 + 1e-4 for v in oklab_to_linear(L, a, b))


def oklch(L, C, h):
    """Gamut-clip chroma by bisection, then return #rrggbb."""
    if not in_gamut(L, C, h):
        lo, hi = 0.0, C
        for _ in range(28):
            mid = (lo + hi) / 2
            if in_gamut(L, mid, h):
                lo = mid
            else:
                hi = mid
        C = lo
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    rgb = oklab_to_linear(L, a, b)
    return "#" + "".join(f"{round(_srgb_encode(v) * 255):02x}" for v in rgb)


def hex_to_linear(hx):
    hx = hx.lstrip("#")
    return tuple(_srgb_decode(int(hx[i:i + 2], 16) / 255) for i in (0, 2, 4))


# ---------------------------------------------------------------- the ladder

# Shared perceptual ladder. Same L for every theme; only hue/chroma differ.
SURFACE = {                  # role            L      chroma multiplier
    "darker_background":  (0.130, 0.55),
    "dark_background":    (0.158, 0.70),
    "background":         (0.180, 0.85),
    "lighter_background": (0.232, 1.00),
    "selection":          (0.300, 1.55),
    "muted":              (0.395, 1.40),
}
TEXT = {
    "dark_foreground":    (0.545, 0.55),
    "light_foreground":   (0.742, 0.32),
    "foreground":         (0.858, 0.22),
    "bright_foreground":  (0.958, 0.14),
}

# Canonical ANSI hue anchors in OKLCH degrees.
ANSI_HUES = {
    "red": 22, "orange": 56, "yellow": 96, "green": 145,
    "cyan": 195, "blue": 252, "magenta": 330,
}
# Per-hue chroma trim so no single ANSI slot screams louder than the rest.
ANSI_CHROMA = {
    "red": 1.00, "orange": 1.00, "yellow": 0.92, "green": 0.86,
    "cyan": 0.84, "blue": 1.00, "magenta": 0.96,
}

ANSI_L = 0.760
ANSI_BRIGHT_L = 0.845
MAX_BEND = 12.0   # degrees; keeps "red" red instead of rotating it into orange

# Per-hue nudges so every ANSI slot reads as the colour it is named after at a
# shared perceptual weight (yellow needs more light, red needs less).
ANSI_TUNE = {                # (dL, chroma x)
    "red":     (-0.030, 1.18),
    "orange":  (-0.010, 1.12),
    "yellow":  (+0.045, 1.02),
    "green":   (+0.005, 0.94),
    "cyan":    (+0.010, 0.90),
    "blue":    (-0.015, 1.12),
    "magenta": (-0.010, 1.06),
}


def _bend(hue, tint, amount, cap=MAX_BEND):
    """Rotate an ANSI hue slightly toward the theme's tint, hard-capped.

    Uncapped, a warm theme drags 'blue' 30 degrees into violet and a teal theme
    turns 'red' into apricot. The cap keeps the family tint readable as a tint.
    """
    d = ((tint - hue + 180) % 360) - 180
    d = max(-cap, min(cap, d * amount))
    return (hue + d) % 360


class Theme:
    FAMILY = "Noct"          # display prefix
    FAMILY_SLUG = "noct"     # directory prefix

    def __init__(self, key, tagline, tint, bg_chroma, accent,
                 ansi_chroma=0.078, bend=0.16, icons="Yaru-dark", hero="1-orbit"):
        self.key = key                                   # short name, used by compose
        self.slug = f"{self.FAMILY_SLUG}-{key}"          # noct-umbra
        self.name = f"{self.FAMILY} {key.capitalize()}"  # Noct Umbra
        self.hero = hero
        self.tagline = tagline
        self.tint = tint                 # hue the whole theme is tinted toward
        self.bg_chroma = bg_chroma       # base chroma for dark surfaces
        self.accent = accent             # (L, C, h)
        self.ansi_chroma = ansi_chroma
        self.bend = bend
        self.icons = icons

    def colors(self):
        c = {"mode": "dark"}
        c["accent"] = oklch(*self.accent)
        for role, (L, mult) in SURFACE.items():
            c[role] = oklch(L, self.bg_chroma * mult, self.tint)
        for role, (L, mult) in TEXT.items():
            c[role] = oklch(L, self.bg_chroma * mult * 2.2, self.tint)
        for nm, h in ANSI_HUES.items():
            dL, cmul = ANSI_TUNE[nm]
            hh = _bend(h, self.tint, self.bend)
            cc = self.ansi_chroma * ANSI_CHROMA[nm] * cmul
            c[nm] = oklch(ANSI_L + dL, cc, hh)
            c["bright_" + nm] = oklch(ANSI_BRIGHT_L + dL * 0.5, cc * 0.94, hh)
        # brown is a low-key earth tone, not a full ANSI slot
        c["brown"] = oklch(0.455, self.ansi_chroma * 0.80, _bend(48, self.tint, 0.30, cap=8))

        # Hairline window borders: the active one carries a faint gradient sheen,
        # the inactive one all but dissolves into the desktop.
        aL, aC, aH = self.accent
        c["hyprland_active_border"] = "rgba(%sff) rgba(%sff) 120deg" % (
            oklch(aL, aC, aH).lstrip("#"),
            oklch(aL - 0.16, aC * 0.72, (aH + 16) % 360).lstrip("#"))
        c["hyprland_inactive_border"] = "rgba(%s99)" % (
            oklch(SURFACE["lighter_background"][0] + 0.03,
                  self.bg_chroma, self.tint).lstrip("#"))
        return c

    def toml(self):
        c = self.colors()
        order = [
            None, "mode", None,
            "accent", "selection", "muted", None,
            "background", "dark_background", "darker_background", "lighter_background", None,
            "foreground", "dark_foreground", "light_foreground", "bright_foreground", None,
            "hyprland_active_border", "hyprland_inactive_border", None,
            "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown", None,
            "bright_red", "bright_yellow", "bright_green",
            "bright_cyan", "bright_blue", "bright_magenta",
        ]
        out = [f"# {self.name} — {self.tagline}",
               "# Generated in OKLCH; all four themes in this family share one contrast ladder.",
               ""]
        for k in order:
            if k is None:
                out.append("")
            elif k == "mode":
                out.append('mode = "dark"')
            else:
                out.append(f'{k} = "{c[k]}"')
        return "\n".join(l for l in out).replace("\n\n\n", "\n\n").strip() + "\n"


THEMES = [
    Theme(
        key="umbra", hero="1-eclipse", tagline="neutral graphite, one lilac signal",
        tint=288, bg_chroma=0.009,
        accent=(0.735, 0.132, 288),
        ansi_chroma=0.080, bend=0.18, icons="Yaru-purple-dark",
    ),
    Theme(
        key="cinder", hero="2-sweep", tagline="warm ink, clay ember",
        tint=52, bg_chroma=0.013,
        accent=(0.722, 0.132, 38),
        ansi_chroma=0.082, bend=0.20, icons="Yaru-wartybrown-dark",
    ),
    Theme(
        key="halcyon", hero="3-terrace", tagline="deep petrol, seafoam light",
        tint=178, bg_chroma=0.016,
        accent=(0.812, 0.108, 172),
        ansi_chroma=0.078, bend=0.18, icons="Yaru-prussiangreen-dark",
    ),
    Theme(
        key="nimbus", hero="4-split", tagline="cold slate, pale steel",
        tint=248, bg_chroma=0.013,
        accent=(0.830, 0.078, 231),
        ansi_chroma=0.074, bend=0.16, icons="Yaru-blue-dark",
    ),
]

BY_SLUG = {t.slug: t for t in THEMES}
BY_KEY = {t.key: t for t in THEMES}

if __name__ == "__main__":
    for t in THEMES:
        print("=" * 60)
        print(t.toml())
