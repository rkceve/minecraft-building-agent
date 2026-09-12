# mcbuild DSL reference (what your build.py may use)

```python
from mcbuild.dsl import Build
from mcbuild.palette import Palette

def build() -> Build:
    b = Build(origin=(0, 1, 0), palette=Palette(...), seed=0)
    ...
    return b
```
Coordinates in the script are LOCAL to `origin` (x east, y up, z south). y=0 in local space is the
floor level (world y=1 when origin y is 1). Faces are named by outward normal: `"n"` = -z, `"s"` = +z,
`"e"` = +x, `"w"` = -x. A `Frame` is a wall face: `u` runs along it (left→right seen from outside),
`v` up from the wall base. All helpers embed the sample cathedral's placements; you decide massing,
proportions, counts and palette.

## Palette
`Palette(primary, secondary, accent, trim, glass, roof, light)` — block ids without `minecraft:`.
- `primary`: wall body (default `calcite`)
- `secondary`: stairs/slabs/walls detail family (default `polished_diorite`; needs a family with stairs+slab)
- `accent`: arches, pillars, outlines, plinth (default `deepslate_bricks`)
- `trim`: wood species for fences/trapdoors/doors/beams (default `pale_oak`)
- `glass`: pane id (default `white_stained_glass_pane`)
- `roof`: roof stairs family (default `deepslate_tiles`)
- `light`: finial block (default `end_rod`)
Families with stairs/slab/wall: stone_bricks, deepslate_bricks, deepslate_tiles, polished_deepslate,
tuff_bricks, polished_tuff, bricks, mud_bricks, cobblestone, mossy_stone_bricks, nether_bricks,
red_nether_bricks, end_stone_bricks, polished_blackstone_bricks, blackstone, sandstone, red_sandstone,
diorite, andesite, granite (polished_* have stairs/slab only), prismarine_bricks, dark_prismarine,
quartz_block, smooth_quartz, purpur_block, cut_copper, oxidized_cut_copper, and any wood species.
`calcite`, `white_concrete` have no variants (fine as primary only).

## Build methods (local coords, inclusive ranges)
Raw (use sparingly):
- `b.box(x0,y0,z0, x1,y1,z1, block, id=None)`; `b.put(x,y,z, block)`; `b.clear(x0,y0,z0, x1,y1,z1)`

Walls and openings:
- `f = b.wall(face, x0,z0, x1,z1, y0, height, thickness=1, depth=True, bay=6, id=None) -> Frame`
  The line (x0,z0)-(x1,z1) must be axis-parallel; `face` is its outward normal. `depth=True` adds the
  sample's relief (plinth course, pilasters every `bay`, string course, recessed panels).
- `b.window(f, u, v, width, height, style="pointed"|"cathedral"|"lancet"|"round"|"rose", mullion=True, id=None)`
  `style="cathedral"` stamps the builder's REAL cathedral window tracery (walls, stairs, slabs, fences,
  trapdoors cut from the reference schematic and cropped to the requested odd width 3..11 and height >= 8).
  Prefer it for Gothic windows when asked for richer or more authentic detail.
  Pointed arch that steps in 1 block every 2 rows; outline + relief frame + sill + glass + tracery.
  `rose`: circular, `width` = diameter (odd). Keep `v >= 2` so the sill fits.
- `b.windows(f, v, width, height, count, style="pointed", id=None)` — evenly spaced, symmetric.
- `b.door(f, u=None, width=2, height=3, id=None)` — pointed-arch double door, centred when `u` is None.
- `b.eave(f, overhang=1, id=None)` — inverted-stair cornice with projecting slab course.
- `b.buttress(f, u, depth=3, height=None, id=None)` — stepped buttress at column `u`.
- `b.pilaster` is applied automatically by `wall(depth=True)`.

Structure:
- `b.corner_pillar(x, z, y0, height, size=3, id=None)` — the sample's ringed pier with bands and pinnacle.
- `b.plinth(x0,z0, x1,z1, y0, height=None, projection=1, id=None)` — foundation base with chamfer.
- `b.beam(x0,z0, x1,z1, y, braces=True, id=None)` — log beam with inverted-stair arch braces at the ends.
- `b.floor(x0,z0, x1,z1, y, id=None)` — checker floor with slab texture and accent border.

Roofs:
- `b.gable_roof(x0,z0, x1,z1, y_base, ridge="x"|"z", overhang=1, id=None)` — stairs-only roof, solid
  underneath, gable ends filled; odd spans get the ridge ornament automatically.
- `b.spire(x0,z0, x1,z1, y_base, height, id=None)` — tapering pyramidal spire with finial.

Composites:
- `frames = b.room(x0,z0, x1,z1, y0, height, thickness=1, pillars=True, eaves=True, plinth=True, id=None)`
  Four walls with relief, corner pillars, eaves, plinth. Returns `{"n": Frame, "s": ..., "e": ..., "w": ...}`.
- `frames = b.tower(x0,z0, x1,z1, y0, height, spire_height=None, id=None)` — room without eaves + spire.

Output / checks:
- `b.check() -> list[str]` warnings: floating blocks, unsupported stairs, windows overlapping pillars,
  even building width (builder's rule: odd widths), out-of-envelope.
- Preview: `python -m mcbuild.preview build.py --faces n,e,s,w`

## Conventions
- Give every important element an `id=` ("nave", "tower_n", "rose") so the player can refer to it.
- Later calls overwrite earlier ones: build walls first, then openings, then pillars/buttresses, then
  roofs, then interior.
- Element sizes that look right at 2:1 scale: wall height 10–16, window width 3–5 / height 7–11,
  pillar size 3, bay 6–8. Towers: make them tall — tower height 1.5–2× the nave wall height, spire height 1.5–2.5× the tower span (Gothic spires are steep; a 7-wide tower wants a 12–16 tall spire).
