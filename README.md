# Noct — an Omarchy theme family

Four minimal dark [Omarchy](https://omarchy.org) themes and the generator that
builds them.

| Theme | Accent | | |
|---|---|---|---|
| **Noct Umbra** | `#a69bf7` | neutral graphite, one lilac signal | [repo](https://github.com/senu-nk/omarchy-noct-umbra-theme) |
| **Noct Cinder** | `#eb8666` | warm ink, clay ember | [repo](https://github.com/senu-nk/omarchy-noct-cinder-theme) |
| **Noct Halcyon** | `#70d8ba` | deep petrol, seafoam light | [repo](https://github.com/senu-nk/omarchy-noct-halcyon-theme) |
| **Noct Nimbus** | `#92d1f1` | cold slate, pale steel | [repo](https://github.com/senu-nk/omarchy-noct-nimbus-theme) |

All four are prefixed `noct-` so they sort together in `omarchy theme list`.

## Install

```bash
omarchy theme install https://github.com/senu-nk/omarchy-noct-umbra-theme
omarchy theme install https://github.com/senu-nk/omarchy-noct-cinder-theme
omarchy theme install https://github.com/senu-nk/omarchy-noct-halcyon-theme
omarchy theme install https://github.com/senu-nk/omarchy-noct-nimbus-theme
```

## How they are built

Nothing here is hand-tuned hex. `palette.py` generates every colour in OKLCH from
one shared perceptual ladder — identical L\* for each background and foreground
role across all four themes — so only hue, chroma and accent change between them.
ANSI hues bend slightly toward each theme's tint, hard-capped at 12° so "red"
never rotates into orange.

`compose.py` builds four wallpapers per theme from signed-distance fields:

| | |
|---|---|
| **eclipse** | An enormous body against a lit field, rimmed on the side facing the light |
| **sweep** | One wide band of light crossing the frame, bright at one end |
| **terrace** | A body rising behind full-width strata |
| **split** | A hard diagonal and a huge circle that inverts where they cross |

Two constraints hold the set together. Every area larger than a hairline carries a
gradient across it — flat saturated planes read as poster paint and fight the
windows on top. And calm comes from a gradient falling off, never from leaving a
rectangle of black, because a hard seam where a composition stops looks unfinished.

`render.py` composites in linear light and only encodes to sRGB at the end, adding
film grain and triangular-PDF dither. Without that last step a near-black gradient
across 3840×2160 bands badly on a large panel.

`compose.gain()` normalises accent light across themes: a pale seafoam accent
carries roughly twice the luminance of a mid lilac one, so the same nominal
brightness would wash one theme and leave another timid.

## Build

Needs Python with `numpy` and `Pillow`.

```bash
python3 build.py staged          # renders all four themes into staged/
cp -r staged/noct-umbra ~/.config/omarchy/themes/
omarchy theme set noct-umbra
```

`python3 preview_sheet.py sheet.png` renders every composition small and tiles
them into one contact sheet — the fast way to judge a change.

To alter a theme, edit its `Theme(...)` entry in `palette.py` or its staging in
`compose.GEOMETRY`, then rebuild. Editing an installed `colors.toml` by hand
desyncs it from the generator and the next build overwrites it.

## License

MIT — see [LICENSE](LICENSE).
