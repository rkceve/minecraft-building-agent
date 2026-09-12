# mcbuild builder DSL — specification (fixed contract)

Astra (the design LLM) writes `build.py` scripts that call this DSL. Every helper embeds placement
patterns read from the reference cathedral (`refs/cathedral.litematic`, by ULLAFNC). The DSL owns
block-state resolution and palette mapping; the script owns massing and composition.

Modules (all under `mcbuild/`): `palette.py`, `blockstate.py`, `techniques.py`, `dsl.py`, `preview.py`.
Voxel type is `Voxels = dict[(x,y,z), str]` from `mcbuild/litematic.py`. Coordinates: x east, y up, z south.
Faces are named by outward normal: `"n"` = -z, `"s"` = +z, `"e"` = +x, `"w"` = -x.

---
## palette.py
```python
@dataclass(frozen=True)
class Palette:
    primary: str = "calcite"            # wall body
    secondary: str = "polished_diorite" # stairs/slabs/walls detail family
    accent: str = "deepslate_bricks"    # arches, pillars, outlines
    trim: str = "pale_oak"              # fences, trapdoors, doors (wood species)
    glass: str = "white_stained_glass_pane"
    roof: str = "deepslate_tiles"       # roof stairs family
    light: str = "end_rod"

FAMILIES: dict[str, dict[str, str]]   # base block -> {"block","stairs","slab","wall"} (missing keys allowed)
def variant(pal: Palette, role: str, kind: str) -> str
```
- `variant(pal, "secondary", "stairs")` returns the stairs block id of that family (e.g. `polished_diorite_stairs`).
  If the family lacks the kind (calcite has no stairs), fall back: primary→secondary→accent→`stone_brick_*`.
- FAMILIES must cover at least: stone_bricks, deepslate_bricks, deepslate_tiles, polished_deepslate, calcite,
  polished_diorite, diorite, andesite, polished_andesite, granite, polished_granite, tuff_bricks, polished_tuff,
  bricks, quartz_block (stairs `quartz_stairs`, slab `quartz_slab`), smooth_quartz, sandstone, smooth_sandstone,
  red_sandstone, blackstone, polished_blackstone_bricks, mud_bricks, cobblestone, mossy_stone_bricks,
  prismarine_bricks, dark_prismarine, nether_bricks, red_nether_bricks, end_stone_bricks, purpur_block,
  white_concrete (no variants), smooth_stone (slab only), cut_copper, oxidized_cut_copper, and every wood
  species (oak, spruce, birch, jungle, acacia, dark_oak, mangrove, cherry, pale_oak, bamboo, crimson, warped)
  with `_planks`, `_stairs`, `_slab`, `_fence`, `_trapdoor`, `_door`, `_log` (bamboo: `bamboo_block`).
- Wood roles: `trim` names a species; `variant(pal, "trim", "fence")` → `pale_oak_fence`, `"trapdoor"`,
  `"door"`, `"planks"`, `"log"`, `"stairs"`, `"slab"`.
- Deterministic; pure functions; a unit test asserts every FAMILIES entry's ids match the regex
  `^[a-z0-9_]+$` and that stairs ids end with `_stairs`, slabs with `_slab`, walls with `_wall`.

## blockstate.py
```python
def stairs(block: str, facing: str, half: str = "bottom", shape: str = "straight") -> str
def slab(block: str, kind: str = "bottom") -> str       # bottom|top|double
def log(block: str, axis: str) -> str                   # x|y|z
def wall(block: str, up: bool = True, **sides) -> str   # sides: north/east/south/west in {none,low,tall}
def fence(block: str, **sides) -> str                   # bool sides -> "true"/"false"
def trapdoor(block: str, facing: str, half: str = "bottom", open: bool = False) -> str
def door(block: str, facing: str, half: str, hinge: str = "left", open: bool = False) -> str
def pane(block: str, **sides) -> str
def rotate_state(block: str, quarter_turns: int) -> str  # rotate facing/axis/side props by 90° CW steps (y axis)
```
- Emit properties in a fixed sorted order; always include `waterlogged=false` for stairs/slabs/walls/fences/trapdoors/panes.
- `facing` for stairs is the direction the stair's *low step points toward*... use Minecraft semantics exactly:
  stairs `facing` = direction the full-height back faces AWAY from, i.e. `facing=north` means the stair rises
  toward north (the tall side is on the north). Provide a helper `stairs_toward(block, outward_face, half)` that
  builds a stair whose HIGH side is toward `outward_face` (used for eaves/roofs) and a test with an explicit
  truth table for all four faces.
- Fence and wall connection sides are *written explicitly* by the DSL (never rely on server updates):
  the DSL has a post-pass `connect_fences_and_walls(vox)` that sets `north/east/south/west` for every fence,
  pane and wall block based on solid or same-type neighbours (wall: `low` when neighbour is a fence/wall/pane/
  air-with-solid-above? keep simple: `low` if neighbour is a wall/fence/pane/full block, else `none`;
  `up=true` if no wall neighbours on opposite sides or if there is a block above; fences: `true` if neighbour is
  a fence or full block).

## techniques.py — the coded patterns (read from the cathedral; relative coordinates)
All functions are pure: they take a `Voxels` dict plus a `Palette` and RETURN a new dict of the blocks to place
(the caller merges, later calls win). All also return provenance: signature `-> Voxels`; the dsl layer tags ids.

Coordinate frame for face-attached techniques: helper `Frame(face, x0, y0, z0, width, height)` where `u` runs
along the face (left→right seen from outside), `v` up, `d` is depth (0 = wall plane, +1 = one block OUTWARD,
-1 = inward). Implement `Frame.world(u, v, d) -> (x,y,z)` and `Frame.turns` (quarter turns for rotate_state).

1. `wall_fill(frame, thickness=1, pal) -> Voxels` — solid `primary` between d = 0 and d = -(thickness-1).

2. `corner_pillar(x, z, y0, height, pal, size=3) -> Voxels` — the cathedral pier: a `size × size` column
   (size 3 default, 2 allowed) whose ring is `variant(secondary,"wall")` and whose core is `primary`
   (pattern `w#w / #C# / w#w` per layer, from the z=19..21 layers at x 60..62). Every 6th layer counting from y0+2
   is a full ring of `accent` (band). Cap: at `height` a layer of `variant(secondary,"slab")` top slabs
   projecting 1 block on all sides (size+2), then at height+1 a `size × size` layer of `accent`, then the
   pinnacle: `pal.light` (end_rod facing=up) on the four corners and a `variant(accent,"wall")` in the centre
   two blocks tall, topped with one more `light`. (Cathedral: `|.|` at y26-27 and `w#w` at y25 around x 60..62.)

3. `pilaster(frame, u, pal, width=1) -> Voxels` — a shallow pier on the wall face at column u: `accent` from
   v=0 to top at d=+1, with a `variant(secondary,"wall")` cap at the top+1 and a `variant(secondary,"slab")`
   bottom slab at v=0 d=+2 as a plinth. Used at bay boundaries by `wall_depth`.

4. `wall_depth(frame, pal, bay=6) -> Voxels` — relief for a plain wall: pilasters every `bay` columns
   (centred so the pattern is symmetric: compute the leftover and split it), a plinth course at v=0..1 of
   `accent` at d=+1 running the full width, and a string course (band) of `variant(secondary,"slab")`
   top slabs at d=+1 at v = height-1 under the eave. Between pilasters every other bay gets a recessed panel:
   d=0 replaced by `secondary` for v in [2, height-3], leaving a 1-block border of primary.

5. `window_frame(frame, u, v, width, height, pal, style="pointed", mullion=True) -> Voxels` — the cathedral
   window (from z=19..21, x 51..59, y 2..23):
   - Opening: air (represented in the returned dict as the special value `"air"` — the merge step deletes
     those keys) inside the arch; below the springing line it is a rectangle of `width` × `spring_h`, above it a
     pointed arch that steps inward 1 block every 2 rows on each side until the two sides meet (odd width: apex
     1 block wide; even width: 2-wide apex). `spring_h = height - ceil(width/2)*2`; if `spring_h < 2` use a
     round-top variant that steps 1 per row (`style="round"` forces this).
   - Jambs and arch outline: `accent` on d=0 (one block outside the opening on both sides and along the arch
     stepping), i.e. the B outline visible in the z=21 layer.
   - Relief frame: the same outline repeated at d=+1 (the z=20 layer shows the B arch one block proud), plus a
     sill: a row of `variant(secondary,"slab")` top slabs at v-1, d=+1 across `width+2`, and under it a row of
     `stairs_toward(secondary, outward, half="top")` at v-2, d=+1 (the cathedral's inverted stairs under
     openings, `^` marks in the z=20 layer).
   - Glazing: `pal.glass` panes filling the opening at d=0 (connection sides set by the post-pass). If
     `mullion` and width >= 5: a central vertical `variant(trim,"fence")` at u+width//2 from v to the springing
     line, and at the springing line a horizontal row of trim trapdoors (`open=true`, facing outward) across the
     opening at d=+1 (the `ttt` rows in the z=22/z=20 layers).
   - `style="lancet"` = pointed, mullion off, width ≤ 3. `style="rose"`: a circular rose window of diameter
     `width` (odd): outline in accent, spokes of `variant(trim,"fence")` every 45°, glass elsewhere, ring of
     `variant(secondary,"wall")` at d=+1 around the outline.

6. `eave(frame, pal, overhang=1) -> Voxels` — cornice at the top of a wall face (cathedral y 24..25 at d=+1..+2,
   `st` pattern): at v = height-1: `stairs_toward(secondary, outward, half="top")` at d=+1 (inverted stairs whose
   high side faces out), and at v = height: `variant(secondary,"slab")` top slabs at d=+1 and (if overhang ≥ 2)
   d=+2, plus a full course of `primary` at d=0. Corners are handled by the dsl (calls on adjacent faces overlap
   at the corner block; last writer wins, then a corner fix sets `shape=outer_left/outer_right` for the two
   stairs meeting at an outside corner — implement `fix_stair_corners(vox)` in blockstate or techniques).

7. `gable_roof(x0, z0, x1, z1, y_base, pal, ridge="x", pitch=1, overhang=1) -> Voxels` — stairs roof:
   for a ridge along x, each row k from the eave upward is a line of `stairs_toward(roof, outward_face,
   "bottom")` on both slopes at y_base+k, z = z0-overhang+k and z1+overhang-k, with `roof` full blocks filling
   under the stair lines (so the roof is solid, no see-through), until the two slopes meet: if they meet on one
   row put a line of `variant(roof,"slab")` bottom slabs at the ridge... use: odd span → ridge is a full block
   line topped by `slab(roof,"bottom")`; even span → two stairs lines back to back. Gable ends (the two
   triangular walls) are filled with `primary` (the dsl passes gable_fill=True by default). Under the eave line
   add one row of `stairs_toward(roof, outward, half="top")` as the eave return.

8. `floor_texture(x0, z0, x1, z1, y, pal, seed=0) -> Voxels` — the cathedral floor (y 0..1 rows `B.B.B`,
   `w.w.w`): a checker with period 2 of `primary` and `secondary`, with a deterministic pseudo-random 15 % of
   `secondary` cells replaced by `variant(secondary,"slab")` **double** slabs (same footprint, visual seam) and a
   border ring (1 block) of `accent`. Deterministic by seed (use `random.Random(seed)`).

9. `buttress(frame, u, pal, depth=3, height=None) -> Voxels` — a stepped buttress against the wall at column u:
   a column of `accent` `width=2` at d=+1..+depth from v=0 up to `height` (default 2/3 of the wall height),
   with `stairs_toward(accent, outward, "bottom")` steps at the top of each depth step (depth decreases by 1
   every `height//depth` rows) and a top slab. Cathedral piers are freestanding; this is the attached version
   used for small churches.

10. `spire(x0, z0, x1, z1, y_base, pal, height) -> Voxels` — pyramidal spire over a square tower footprint:
    each level shrinks by 1 on each side every `max(1, round(height / (span/2)))` rows using
    `stairs_toward(roof, outward, "bottom")` on the four edges and `roof` block fill inside, ending with
    a `variant(roof,"wall")` 2 tall and one `light` on top (the cathedral pinnacle motif).

11. `door_opening(frame, u, pal, width=2, height=3) -> Voxels` — opening with a pointed arch (same stepping as
    window), `accent` outline, `variant(trim,"door")` lower/upper halves facing outward (hinge left/right for a
    double door when width==2), a `stairs_toward(secondary, outward, "bottom")` step at v=-1 d=+1 across width+2.

12. `connect_fences_and_walls(vox)` and `fix_stair_corners(vox)` post-passes as described in blockstate.

## dsl.py — what Astra imports
```python
class Build:
    def __init__(self, origin=(0, 1, 0), palette: Palette | None = None, seed: int = 0): ...
    palette: Palette
    # raw
    def box(self, x0,y0,z0, x1,y1,z1, block: str, id: str | None = None) -> None  # inclusive, local coords
    def put(self, x,y,z, block: str, id=None) -> None
    def clear(self, x0,y0,z0, x1,y1,z1) -> None
    # elements (all local coords; the Build applies techniques immediately; later calls overwrite earlier)
    def wall(self, face: str, x0, z0, x1, z1, y0, height, thickness=1, depth=True, bay=6, id=None) -> Frame
        # x0,z0..x1,z1 must be a line parallel to an axis; `face` is its outward normal
    def window(self, frame: Frame, u, v, width, height, style="pointed", mullion=True, id=None) -> None
    def windows(self, frame: Frame, v, width, height, count, style="pointed", id=None) -> None
        # evenly spaced and symmetric on the frame; the DSL computes the u positions
    def door(self, frame: Frame, u=None, width=2, height=3, id=None) -> None   # u=None → centred
    def corner_pillar(self, x, z, y0, height, size=3, id=None) -> None
    def buttress(self, frame: Frame, u, depth=3, height=None, id=None) -> None
    def eave(self, frame: Frame, overhang=1, id=None) -> None
    def gable_roof(self, x0,z0,x1,z1, y_base, ridge="x", overhang=1, id=None) -> None
    def spire(self, x0,z0,x1,z1, y_base, height, id=None) -> None
    def floor(self, x0,z0,x1,z1, y, id=None) -> None
    # composites
    def room(self, x0,z0,x1,z1, y0, height, thickness=1, pillars=True, eaves=True, id=None) -> dict[str, Frame]
        # four walls (faces n/e/s/w) with wall_depth, corner pillars at the 4 corners (height+1), eaves; returns frames by face
    def tower(self, x0,z0,x1,z1, y0, height, spire_height=None, id=None) -> dict[str, Frame]
        # room without eaves + spire (default spire_height = span)
    # output
    def voxels(self) -> Voxels               # WORLD coordinates (origin applied), post-passes applied
    def provenance(self) -> dict[tuple[int,int,int], str]   # world pos -> element id
    def elements(self) -> dict[str, dict]    # id -> {"kind", "args", "bbox"}
```
- Element ids: explicit `id=` or auto `f"{kind}_{n}"`. Every voxel written by an element call is tagged.
- `Frame` objects returned by `wall`/`room`/`tower` are what windows/doors/eaves attach to.
- `Build.voxels()` applies `connect_fences_and_walls` then `fix_stair_corners`, drops `"air"` markers.
- Validation: `Build.check() -> list[str]` returns warnings: floating single blocks, stairs with no support,
  windows overlapping pillars, elements outside a 64×64×64 envelope.

## preview.py
```
python -m mcbuild.preview build.py [--faces n,s,e,w] [--json out.json]
```
Loads the script (it must define `def build() -> Build`), prints block count, palette, element list with
bboxes, `check()` warnings, and ASCII elevations (`mcbuild.ascii.elevation`) for the requested faces.
`--json` dumps voxels + provenance for the apply step.

## Reference script (tests/fixtures/chapel.py) — must run and pass `check()` with no errors
A small chapel: `room` 15×25 walls height 12 at y0=1, 3 pointed windows per long side (width 3, height 7, v=3),
a rose window (diameter 5) on the front gable, a door centred on the front, buttresses at the window
boundaries, gable roof ridge along z, floor. Its ASCII elevations are the acceptance test: pointed arches
visible, pillars at corners, eave line, roof stairs continuous with no holes (run-length check: every roof
row is contiguous), gable ends filled.
