# 16×16 Cyberpunk — LED matrix art

Pixel art and animation for a 16×16 RGB LED panel (WS2812B / HUB75 / Pixoo /
etc.) — a Japanese-cyberpunk pair, a Matrix rain loop, two landscapes,
the Eye of Sauron, and a colour-cycling TIE fighter.
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

### Matrix rain — `generate_matrix.py`

Sixteen columns of falling code: a blown-out leader pixel with a green trail
fading behind it, and the glyph-flicker of characters changing mid-fall.
32 frames at 80 ms (2.6 s loop).

![matrix rain](matrix16_anim_preview.gif)

This one is procedural — each frame is drawn from the column state at time
`t` rather than authored pixel by pixel. Column heads travel a 32-row cycle
at whole rows per frame, so every column is back where it started on the last
frame and the loop closes with no visible seam. The flicker noise is hashed
from `(x, y, t)` for the same reason: it repeats with the loop instead of
popping at the wrap. `matrix16.png` is frame 0, if you want a still.

### Moonlit hills — `generate_moon.py`

A full moon over two rolling hills with a lone tree on the far ridge. Wisps of
cloud drift across the sky, stars twinkle out of phase with each other, and
fireflies blink above the ridgeline. 32 frames at 120 ms (3.8 s loop).

![moonlit hills](moon16_anim_preview.gif)

Only one wisp runs at a height that crosses the disc, so the moon is clear for
half the loop and veiled as that wisp drifts past — a cloud over the moon
brightens rather than darkens, which is what sells it as thin cloud. Drift is
one pixel every other frame, carrying a wisp exactly 16 px over the loop so it
wraps seamlessly. The ridgelines are hand-written per column: at 16 px wide,
placing each crest by hand beats any curve formula.

### Wooded forest — `generate_forest.py`

Layered trunks receding into a misty gap of light, a dappled canopy overhead,
and two shafts of sun cutting down between the trees. Motes drift up through
the beams, the canopy stirs, and a leaf falls the height of the panel each
loop. 32 frames at 110 ms (3.5 s loop).

![forest](forest16_anim_preview.gif)

Depth comes from two things: near trunks are warm and dark while far ones
desaturate toward the mist, and the mist itself shades by distance from the
gap so light falls off in every direction instead of banding by row. The leaf
texture is hashed on position alone — hashing it on the frame number too made
the entire canopy boil — so wind is just a handful of pixels stirring a step
brighter per frame.

### The Eye — `generate_eye.py`

The lidless eye wreathed in flame above the dark spire of Barad-dûr. Fire
licks around the rim, the glow behind it swells, and the slit pupil sweeps
left and right, searching. 24 frames at 100 ms (2.4 s loop).

![the eye](eye16_anim_preview.gif)

The eye is a lens — the overlap of two circles — rather than an ellipse,
which is what gives it points at the corners instead of reading as a blob.
The pupil is a single pixel wide with white-hot flanks across the middle
rows only: two pixels of black swallowed the eye, and flanking its full
height turned the iris into a bright capsule.

### TIE fighter — `generate_tie.py`

A TIE silhouette cycling through the spectrum: 32 frames at 110 ms (3.5 s
loop), one full turn of the colour wheel.

![tie fighter](tie16_anim_preview.gif)

The most literal palette animation in the set — the geometry never changes at
all. Every frame draws the same mask and only rotates the hue, so the hull,
its rim light, the wing spars and the backglow all stay in step because they
are derived from one hue value per frame.

A TIE is the Star Wars shape that survives 16 px: two slab wings and a ball,
all straight lines and hard corners. A Vader helmet was the first attempt and
had to be abandoned — at this size the dome, lenses and grille collapse into a
generic face.

## Files

Each piece `<name>` (`torii16`, `oni16`, `matrix16`, `moon16`, `forest16`,
`eye16`, `tie16`) exports the same set:

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
| `<name>_anim.h` | `<name>_anim_rgb888[frames][256]`, `<name>_anim_rgb565[frames][256]`, and `*_FRAMES` / `*_DELAY_MS` defines |

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
- The rain is the one piece built on brightness alone rather than hue: a
  single green with a steep 8-step ramp. The first two steps drop hard, since
  a gentle fade off the leader reads as a fat blur rather than a falling
  glyph once the panel's gamma gets hold of it.
- Because the art is a character grid over a palette, animation is mostly
  palette animation: the geometry stays put and only the meaning of its colors
  changes per frame. The blink is a palette swap too — a 1px-tall eyelid would
  read as noise, so the eyes simply drop to brow-black.
- Silhouettes need something bright behind them. The tree on the moonlit hills
  only became visible once the horizon band was lifted and its moon-facing
  edge was given a rim pixel — black on near-black is just a hole in the
  panel.
- Shafts of light need width. A one-pixel beam vanishes into the haze it is
  cutting through, so the forest's are two px wide with a brighter leading
  edge.
- Fire is the one place per-pixel noise should re-roll every frame. The same
  trick that ruined the forest canopy is exactly what makes the Eye's rim
  read as flame.
- A flat single-colour silhouette needs a rim light along one edge or it has
  no form at all. One edge — running it down the side as well just puts a
  stripe through the shape.

## Editing

Edit the drawing calls in a generator and re-run it; its outputs are
regenerated together.

```sh
pip install Pillow
python3 generate_torii.py    # each script also prints its grid as ASCII
python3 generate_oni.py      # for a quick sanity check in the terminal
python3 generate_matrix.py
python3 generate_moon.py
python3 generate_forest.py
python3 generate_eye.py
python3 generate_tie.py
```
