# 16×16 Japanese Cyberpunk — LED matrix art

Pixel art drawn for a 16×16 RGB LED panel (WS2812B / HUB75 / Pixoo / etc.).
Each piece is generated from code, so the drawing stays editable and every
export format is rebuilt from one source of truth.

## The pieces

### Torii — `generate_torii.py`

A neon torii gate silhouetted against a rising red sun, framed by a dark
skyline with cyan windows and a wet neon-lit street.

![torii](torii16_preview.png)

### Oni — `generate_oni.py`

A red oni glaring out of the dark: bone horns, heavy brows, blown-out cyan
eyes, and a tusked grin, with magenta and cyan rim lights tracing the jaw.

![oni](oni16_preview.png)

Animated: 24 frames at 90 ms (2.2 s loop). The glare breathes from steady cyan
up to a white-hot core and the halo swells with it, the two neon rim lights
stutter out of phase like failing tubes, a single frame tears the eye rows
sideways, and the oni blinks once per loop.

![oni animated](oni16_anim_preview.gif)

## Files

Each piece `<name>` (`torii16`, `oni16`) exports the same set:

| File | What it is |
| --- | --- |
| `<name>.png` | The actual 16×16 image — load this on the panel |
| `<name>_preview.png` | 32× blow-up with a grid, for eyeballing pixels |
| `<name>.json` | `rows_hex` (16 strings of 16 `RRGGBB`) + `pixels_rgb` nested arrays |
| `<name>.h` | C header with `<name>_rgb888[256]` and `<name>_rgb565[256]` |

Animated pieces add:

| File | What it is |
| --- | --- |
| `<name>_anim.gif` | The 16×16 loop |
| `<name>_anim_preview.gif` | 32× blow-up of the loop |
| `<name>_anim.json` | `frames_rows_hex` plus `frame_count` and `delay_ms` |
| `<name>_anim.h` | `<name>_anim_rgb888[24][256]`, `<name>_anim_rgb565[24][256]`, and `*_FRAMES` / `*_DELAY_MS` defines |

On a microcontroller use the RGB565 array and step one frame per
`*_DELAY_MS`; the RGB888 copy is there for hosts that want the full range.

`pixelart.py` holds the shared `Canvas` — drawing primitives (`put`, `rect`,
`disc`, `ring`, `mirror_x`) over a character grid plus a palette, and the
exporters for both the stills and the animation.

All data is row-major from the top-left pixel. If your panel is wired in a
serpentine (boustrophedon) layout, reverse every odd row when writing it out.

## Design notes for LED panels

- Around a dozen colors per piece, all far apart in hue and brightness — LEDs
  crush subtle gradients, so anything more would smear together.
- Large shapes get a 3-step ramp (the sun's deep red → orange-red → amber
  core) so they still read as round after the panel's gamma flattens them.
- Hues are separated, not just brightnesses: torii magenta against sun orange,
  cyan eyes against a red face. Both survive at low panel brightness.
- The oni's magenta/cyan rim lights do the work an outline would do — at 16×16
  there is no room for a border, but two lit edges still detach the silhouette
  from the background.
- Backgrounds are near-black rather than pure black, which keeps dark areas
  from looking like dead pixels.
- Because the art is a character grid over a palette, animation is mostly
  palette animation: the geometry stays put and only the meaning of its colors
  changes per frame. The blink is a palette swap too — a 1px-tall eyelid would
  read as noise, so the eyes simply drop to brow-black.

## Editing

Edit the drawing calls in a generator and re-run it; its outputs are
regenerated together.

```sh
pip install Pillow
python3 generate_torii.py   # each script also prints its grid as ASCII
python3 generate_oni.py     # for a quick sanity check in the terminal
```
