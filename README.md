# 16×16 Japanese Cyberpunk — LED matrix art

A neon torii gate against a rising red sun, framed by a skyline of dark towers
with cyan windows, over a wet neon-lit street. Drawn for a 16×16 RGB LED panel
(WS2812B / HUB75 / Pixoo / etc.).

![preview](torii16_preview.png)

## Files

| File | What it is |
| --- | --- |
| `torii16.png` | The actual 16×16 image — load this on the panel |
| `torii16_preview.png` | 32× blow-up with a grid, for eyeballing pixels |
| `torii16.json` | `rows_hex` (16 strings of 16 `RRGGBB`) + `pixels_rgb` nested arrays |
| `torii16.h` | C header with `torii16_rgb888[256]` and `torii16_rgb565[256]` |
| `generate.py` | The generator — the drawing is code, not a bitmap |

All data is row-major from the top-left pixel. If your panel is wired in a
serpentine (boustrophedon) layout, reverse every odd row when writing it out.

## Design notes for LED panels

- 13 colors total, all far apart in hue and brightness — LEDs crush subtle
  gradients, so anything more would smear together.
- The sun is a 3-step ramp (deep red → orange-red → amber core) so it still
  reads as round after the panel's gamma flattens it.
- Torii magenta and sun orange are separated in hue, not just brightness,
  which keeps the gate visible even at low panel brightness.
- Background is near-black rather than pure black, which keeps the night sky
  from looking like dead pixels.

## Editing

Edit the drawing calls in `generate.py` and re-run it; every output file is
regenerated together.

```sh
pip install Pillow
python3 generate.py   # also prints the grid as ASCII for a quick sanity check
```
