# Astra run v1 — summary (raw log withheld: it contains sandbox filesystem listings)

```
Reading prompt from stdin...
OpenAI Codex v0.153.4
--------
workdir: C:\Users\<user>\mcbuild\experiments\plain_astra
model: gpt-6-astra
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
reasoning summaries: none
session id: 01a09663-ee95-7243-a678-c2216e0d66f1
--------
```

- exec calls: 11
- tokens used: 32,233
- wall time: 7m6.185s

## Astra's messages (in order)

- I’ll build the twin spires, three-arch porch, rose window, and red stair-block roofs, then run the file to verify it.
- The layout now fits within 30 × 47 blocks, with spire crosses reaching y = 33. I’m adding the Gothic window tracery, connected roof sections, and a simple furnished interior.
  
  apply patch
  patch: completed
  C:\Users\<user>\mcbuild\experiments\plain_astra\church_plain.py
  diff --git a/church_plain.py b/church_plain.py
  new file mode 100644
  index 0000000000000000000000000000000000000000..20a5af486d3bd62b02f63357555cbe8c151e32ac
  --- /dev/null
  +++ b/church_plain.py
  @@ -0,0 +1,304 @@
  +"""Old Catholic Shimizu Church, approximately 2 blocks per metre.
  +
  +The three-arched west front faces -Z.  Bounds: X 0..29, Y 0..33,
  +Z 0..46.  Call build() for the complete, deterministic Java block map.
  +"""
  +
  +import math
  +
  +
  +def build() -> dict[tuple[int, int, int], str]:
  +    blocks: dict[tuple[int, int, int], str] = {}
  +    white = "white_concrete"
  +    stone = "smooth_quartz"
  +
  +    def put(x, y, z, block):
  +        blocks[x, y, z] = block
  +
  +    def box(x0, x1, y0, y1, z0, z1, block):
  +        for x in range(x0, x1 + 1):
  +            for y in range(y0, y1 + 1):
  +                for z in range(z0, z1 + 1):
  +                    put(x, y, z, block)
  +
  +    def erase(x, y, z):
  +        blocks.pop((x, y, z), None)
  +
  +    def stair(material, facing, half="bottom", shape="straight"):
  +        return f"{material}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"
  +
  +    def slab(material, kind="bottom"):
  +        return f"{material}_slab[type={kind},waterlogged=false]"
  +
  +    def uv(u, y, plane, axis, block):
  +        x, z = (u, plane) if axis == "z" else (plane, u)
  +        if block is None:
  +            erase(x, y, z)
  +        else:
  +            put(x, y, z, block)
  +
  +    def lancet(center, bottom, spring, tip, plane, axis="z", width=3,
  +               glass=True, dark=False):
  +        """Pointed opening with a solid, one-voxel carved surround."""
  +        radius = width // 2
  +        for y in range(bottom - 1, tip + 2):
  +            for u in range(center - radius - 1, center + radius + 2):
  +                uv(u, y, plane, axis, stone)
  +        for y in range(bottom, tip + 1):
  +            r = radius if y <= spring else int(radius * (tip - y) / (tip - spring))
  +            for u in range(center - r, center + r + 1):
  +                if dark:
  +                    block = "dark_oak_planks"
  +                elif glass:
  +                    color = ("blue", "purple", "red", "cyan")[(y + u) % 4]
  +                    block = f"{color}_stained_glass"
  +                    if u == center and y < spring:
  +                        block = "gray_stained_glass"
  +                else:
  +                    block = None
  +                uv(u, y, plane, axis, block)
  +
  +    def quatrefoil(center, y, plane, axis="z"):
  +        for du, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
  +            uv(center + du, y + dy, plane, axis,
  +               "gray_stained_glass" if du == dy == 0 else "light_blue_stained_glass")
  +
  +    # Ground, continuous foundations, and the raised timber nave floor.
  +    box(0, 29, 0, 0, 0, 46, "grass_block")
  +    box(2, 27, 1, 1, 2, 10, "smooth_stone")
  +    box(3, 26, 1, 1, 10, 42, "stone_bricks")
  +    box(4, 25, 1, 1, 11, 41, "spruce_planks")
  +    box(26, 28, 1, 1, 11, 40, "stone_bricks")
  +    box(8, 21, 1, 1, 42, 46, "stone_bricks")
  +    box(9, 20, 1, 1, 43, 45, "spruce_planks")
  +    box(4, 25, 1, 1, 0, 0, slab("smooth_stone"))
  +    box(3, 26, 1, 1, 1, 1, stair("quartz", "south"))
  +
  +    # Nave shell and the porch's rear wall, with a working double door.
  +    box(3, 3, 2, 13, 10, 42, white)
  +    box(26, 26, 2, 13, 10, 42, white)
  +    box(3, 26, 2, 13, 42, 42, white)
  +    box(3, 26, 2, 17, 10, 10, white)
  +    lancet(14, 2, 5, 8, 10, width=5, dark=True)
  +    for x, hinge in ((14, "left"), (15, "right")):
  +        for y, half in ((2, "lower"), (3, "upper")):
  +            put(x, y, 10,
  +                f"dark_oak_door[facing=north,half={half},hinge={hinge},open=false,powered=false]")
  +    for x in (6, 23):
  +        lancet(x, 3, 5, 7, 10, width=3)
  +
  +    # Three deep pointed arcade openings; clear space is carved through
  +    # the full two-block wall thickness, leaving a sheltered walkable porch.
  +    box(2, 27, 2, 9, 2, 3, white)
  +    box(2, 3, 2, 9, 4, 9, white)
  +    box(26, 27, 2, 9, 4, 9, white)
  +    arches = ((4, 9, 5, 8), (11, 18, 6, 9), (20, 25, 5, 8))
  +    for lo, hi, spring, tip in arches:
  +        for y in range(2, tip + 1):
  +            inset = max(0, y - spring)
  +            for x in range(lo + inset, hi - inset + 1):
  +                for z in (2, 3):
  +                    erase(x, y, z)
  +            if y > spring:
  +                put(lo + inset - 1, y, 2, stair("quartz", "east", "top"))
  +                put(hi - inset + 1, y, 2, stair("quartz", "west", "top"))
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 2, 6, 2, 2, "quartz_pillar[axis=y]")
  +        put(x, 2, 1, stone)
  +        put(x, 6, 1, stair("quartz", "south", "top"))
  +    for plane in (2, 3, 26, 27):
  +        lancet(7, 2, 4, 7, plane, axis="x", width=3, glass=False)
  +    box(2, 27, 9, 9, 4, 9, "birch_planks")
  +    for x in (6, 23):
  +        put(x, 8, 6, "lantern[hanging=true,waterlogged=false]")
  +
  +    # Front upper storey, projecting cornices, pilasters and rose tracery.
  +    box(2, 27, 10, 16, 2, 3, white)
  +    box(2, 3, 10, 16, 4, 10, white)
  +    box(26, 27, 10, 16, 4, 10, white)
  +    box(1, 28, 9, 9, 1, 3, stone)
  +    box(1, 28, 16, 16, 1, 3, stone)
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 10, 15, 1, 1, "quartz_pillar[axis=y]")
  +    for x in (6, 23):
  +        for z in (2, 3):
  +            lancet(x, 10, 13, 15, z)
  +    for x in range(10, 20):
  +        for y in range(9, 17):
  +            dx, dy = x - 14.5, y - 12.5
  +            distance = math.hypot(dx, dy)
  +            if distance <= 3.8:
  +                material = stone
  +                if distance < 3.15:
  +                    material = "gray_stained_glass"
  +                    for n in range(6):
  +                        angle = n * math.tau / 6 + math.pi / 2
  +                        if math.hypot(dx - 2 * math.cos(angle),
  +                                      dy - 2 * math.sin(angle)) < 1.12:
  +                            material = ("red_stained_glass" if n % 2 == 0
  +                                        else "purple_stained_glass")
  +                    if distance < 1:
  +                        material = "magenta_stained_glass"
  +                for z in (2, 3):
  +                    put(x, y, z, material)
  +    # Small round lights above the outer arcade openings.
  +    for x in (5, 8, 21, 24):
  +        for z in (2, 3):
  +            put(x, 8, z, "cyan_stained_glass")
  +    box(1, 28, 17, 17, 1, 10, stone)
  +    box(2, 27, 18, 18, 2, 3, white)
  +    for x in range(3, 28, 2):
  +        put(x, 18, 1, stair("quartz", "south", "top"))
  +    box(1, 28, 19, 19, 1, 3, slab("smooth_quartz"))
  +
  +    # Four rhythmic nave bays: tall lancets, paired round clerestory lights,
  +    # square buttresses and continuous white eave moldings.
  +    for z in (15, 23, 31, 39):
  +        lancet(z, 3, 8, 10, 3, axis="x", width=3)
  +        for off in (-2, 2):
  +            quatrefoil(z + off, 12, 3, axis="x")
  +        lancet(z, 9, 11, 12, 26, axis="x", width=3)
  +    for z in (11, 19, 27, 35, 42):
  +        for x in (2, 27):
  +            box(x, x, 2, 12, z, z, white)
  +            put(x, 13, z, stair("quartz", "east" if x == 2 else "west"))
  +    for x in (2, 3, 26, 27):
  +        box(x, x, 13, 13, 10, 43, stone)
  +    for z in range(12, 43, 2):
  +        put(2, 12, z, stair("quartz", "east", "top"))
  +        put(27, 12, z, stair("quartz", "west", "top"))
  +
  +    # The tiled gable uses stair courses facing uphill.  Intermediate
  +    # horizontal courses allow the broad roof's 2:3 pitch at this scale.
  +    def roof_height(x):
  +        return 14 + (min(x - 2, 27 - x) * 2) // 3
  +
  +    for x in range(2, 28):
  +        h = roof_height(x)
  +        for z in range(9, 44):
  +            put(x, h - 1, z, "red_terracotta")
  +            uphill = x + 1 if x < 14 else x - 1
  +            rising = roof_height(uphill) > h
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if rising else "bricks")
  +        for z in (10, 42):
  +            if 3 <= x <= 26:
  +                box(x, x, 14, h - 1, z, z, white)
  +    box(14, 15, 23, 23, 9, 43, slab("brick"))
  +    for z in (9, 43):
  +        for x in range(2, 28):
  +            put(x, roof_height(x) - 1, z, stone)
  +
  +    # Low lean-to aisle along the east side; its roof intersects the nave
  +    # wall, and its outer windows remain below the tiled roof.
  +    box(28, 28, 2, 7, 11, 40, white)
  +    box(26, 28, 2, 9, 11, 11, white)
  +    box(26, 28, 2, 9, 40, 40, white)
  +    for z in (16, 24, 32, 37):
  +        lancet(z, 3, 5, 6, 28, axis="x", width=1)
  +    for x in range(26, 30):
  +        h = 10 - (x - 26)
  +        for z in range(10, 42):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "west"))
  +    # Clear access from the nave into the narrow aisle.
  +    for z in (20, 21):
  +        for y in (2, 3, 4):
  +            erase(26, y, z)
  +
  +    # Rear sacristy, with a smaller complete red gable and an open interior
  +    # connection to the chancel.
  +    box(8, 8, 2, 7, 42, 46, white)
  +    box(21, 21, 2, 7, 42, 46, white)
  +    box(8, 21, 2, 7, 46, 46, white)
  +    lancet(14, 3, 5, 7, 46, width=3)
  +    for x in range(7, 23):
  +        h = 8 + min(x - 7, 22 - x) // 2
  +        for z in range(42, 47):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if min(x - 7, 22 - x) % 2 else "bricks")
  +        if 8 <= x <= 21:
  +            box(x, x, 8, h - 1, 46, 46, white)
  +    for x in (14, 15):
  +        for z in range(42, 47):
  +            put(x, 12, z, slab("brick"))
  +    for x in range(13, 17):
  +        for y in range(2, 5):
  +            erase(x, y, 42)
  +
  +    # Twin square belfries.  Solid louver blocks close each opening, with
  +    # thin horizontal dark-oak slats on the exposed face.
  +    for cx in (6, 23):
  +        lo, hi = cx - 3, cx + 3
  +        box(lo, hi, 18, 18, 3, 9, stone)
  +        for y in range(19, 23):
  +            for x in range(lo, hi + 1):
  +                for z in range(3, 10):
  +                    if x in (lo, hi) or z in (3, 9):
  +                        put(x, y, z, white)
  +        for plane in (3, 9):
  +            lancet(cx, 19, 20, 22, plane, width=3, dark=True)
  +        for plane in (lo, hi):
  +            lancet(6, 19, 20, 22, plane, axis="x", width=3, dark=True)
  +        for y in (19, 20, 21):
  +            put(cx, y, 2, slab("dark_oak", "top"))
  +        box(lo - 1, hi + 1, 23, 23, 2, 10, stone)
  +        # Seven-block tall pyramids: vertical courses alternate with
  +        # inward steps; inner-corner stair states close the four hips.
  +        radii = (3, 3, 2, 2, 1, 1, 0)
  +        for y, r in enumerate(radii, 24):
  +            box(cx - r, cx + r, y, y, 6 - r, 6 + r, "polished_deepslate")
  +            if r:
  +                for d in range(-r + 1, r):
  +                    put(cx + d, y, 6 - r, stair("polished_deepslate", "south"))
  +                    put(cx + d, y, 6 + r, stair("polished_deepslate", "north"))
  +                    put(cx - r, y, 6 + d, stair("polished_deepslate", "east"))
  +                    put(cx + r, y, 6 + d, stair("polished_deepslate", "west"))
  +                for dx, dz, facing, shape in (
  +                    (-r, -r, "south", "inner_left"),
  +                    (r, -r, "south", "inner_right"),
  +                    (-r, r, "north", "inner_right"),
  +                    (r, r, "north", "inner_left"),
  +                ):
  +                    put(cx + dx, y, 6 + dz, stair("polished_deepslate", facing, shape=shape))
  +        # Four white pinnacles rise directly from each tower's cornice.
  +        for x in (lo - 1, hi + 1):
  +            for z in (2, 10):
  +                put(x, 24, z, stone)
  +                put(x, 25, z,
  +                    "diorite_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
  +        for y in range(31, 34):
  +            connections = "east=true,north=false,south=false,west=true" if y == 32 else "east=false,north=false,south=false,west=false"
  +            put(cx, y, 6, f"iron_bars[{connections},waterlogged=false]")
  +        put(cx - 1, 32, 6, "iron_bars[east=true,north=false,south=false,west=false,waterlogged=false]")
  +        put(cx + 1, 32, 6, "iron_bars[east=false,north=false,south=false,west=true,waterlogged=false]")
  +
  +    # Simple sanctuary: central aisle, paired banks of pews, altar and
  +    # exposed transverse timber ties attached to the nave walls.
  +    box(13, 16, 2, 2, 11, 36, "red_carpet")
  +    for z in range(15, 34, 4):
  +        for lo, hi in ((6, 11), (18, 23)):
  +            box(lo, hi, 2, 2, z, z, stair("dark_oak", "north"))
  +            put(lo, 2, z - 1, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
  +            put(hi, 2, z - 1, "dark_oak_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
  +    box(8, 21, 2, 2, 37, 41, "smooth_quartz")
  +    box(12, 17, 3, 3, 39, 40, "quartz_bricks")
  +    box(12, 17, 4, 4, 39, 40, slab("smooth_quartz"))
  +    for y in range(5, 10):
  +        put(14, y, 41, "dark_oak_log[axis=y]")
  +    box(12, 16, 8, 8, 41, 41, "dark_oak_log[axis=x]")
  +    for z in (14, 22, 30, 38):
  +        box(4, 25, 13, 13, z, z, "dark_oak_log[axis=x]")
  +        for x in (10, 19):
  +            put(x, 12, z, "chain[axis=y,waterlogged=false]")
  +            put(x, 11, z, "lantern[hanging=true,waterlogged=false]")
  +
  +    assert all(0 <= x < 30 and 0 <= y < 34 and 0 <= z < 47
  +               for x, y, z in blocks)
  +    assert all(block != "air" for block in blocks.values())
  +    return blocks
  +
  +
  +if __name__ == "__main__":
  +    print(len(build()))
  
  diff --git a/church_plain.py b/church_plain.py
  new file mode 100644
  index 0000000000000000000000000000000000000000..20a5af486d3bd62b02f63357555cbe8c151e32ac
  --- /dev/null
  +++ b/church_plain.py
  @@ -0,0 +1,304 @@
  +"""Old Catholic Shimizu Church, approximately 2 blocks per metre.
  +
  +The three-arched west front faces -Z.  Bounds: X 0..29, Y 0..33,
  +Z 0..46.  Call build() for the complete, deterministic Java block map.
  +"""
  +
  +import math
  +
  +
  +def build() -> dict[tuple[int, int, int], str]:
  +    blocks: dict[tuple[int, int, int], str] = {}
  +    white = "white_concrete"
  +    stone = "smooth_quartz"
  +
  +    def put(x, y, z, block):
  +        blocks[x, y, z] = block
  +
  +    def box(x0, x1, y0, y1, z0, z1, block):
  +        for x in range(x0, x1 + 1):
  +            for y in range(y0, y1 + 1):
  +                for z in range(z0, z1 + 1):
  +                    put(x, y, z, block)
  +
  +    def erase(x, y, z):
  +        blocks.pop((x, y, z), None)
  +
  +    def stair(material, facing, half="bottom", shape="straight"):
  +        return f"{material}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"
  +
  +    def slab(material, kind="bottom"):
  +        return f"{material}_slab[type={kind},waterlogged=false]"
  +
  +    def uv(u, y, plane, axis, block):
  +        x, z = (u, plane) if axis == "z" else (plane, u)
  +        if block is None:
  +            erase(x, y, z)
  +        else:
  +            put(x, y, z, block)
  +
  +    def lancet(center, bottom, spring, tip, plane, axis="z", width=3,
  +               glass=True, dark=False):
  +        """Pointed opening with a solid, one-voxel carved surround."""
  +        radius = width // 2
  +        for y in range(bottom - 1, tip + 2):
  +            for u in range(center - radius - 1, center + radius + 2):
  +                uv(u, y, plane, axis, stone)
  +        for y in range(bottom, tip + 1):
  +            r = radius if y <= spring else int(radius * (tip - y) / (tip - spring))
  +            for u in range(center - r, center + r + 1):
  +                if dark:
  +                    block = "dark_oak_planks"
  +                elif glass:
  +                    color = ("blue", "purple", "red", "cyan")[(y + u) % 4]
  +                    block = f"{color}_stained_glass"
  +                    if u == center and y < spring:
  +                        block = "gray_stained_glass"
  +                else:
  +                    block = None
  +                uv(u, y, plane, axis, block)
  +
  +    def quatrefoil(center, y, plane, axis="z"):
  +        for du, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
  +            uv(center + du, y + dy, plane, axis,
  +               "gray_stained_glass" if du == dy == 0 else "light_blue_stained_glass")
  +
  +    # Ground, continuous foundations, and the raised timber nave floor.
  +    box(0, 29, 0, 0, 0, 46, "grass_block")
  +    box(2, 27, 1, 1, 2, 10, "smooth_stone")
  +    box(3, 26, 1, 1, 10, 42, "stone_bricks")
  +    box(4, 25, 1, 1, 11, 41, "spruce_planks")
  +    box(26, 28, 1, 1, 11, 40, "stone_bricks")
  +    box(8, 21, 1, 1, 42, 46, "stone_bricks")
  +    box(9, 20, 1, 1, 43, 45, "spruce_planks")
  +    box(4, 25, 1, 1, 0, 0, slab("smooth_stone"))
  +    box(3, 26, 1, 1, 1, 1, stair("quartz", "south"))
  +
  +    # Nave shell and the porch's rear wall, with a working double door.
  +    box(3, 3, 2, 13, 10, 42, white)
  +    box(26, 26, 2, 13, 10, 42, white)
  +    box(3, 26, 2, 13, 42, 42, white)
  +    box(3, 26, 2, 17, 10, 10, white)
  +    lancet(14, 2, 5, 8, 10, width=5, dark=True)
  +    for x, hinge in ((14, "left"), (15, "right")):
  +        for y, half in ((2, "lower"), (3, "upper")):
  +            put(x, y, 10,
  +                f"dark_oak_door[facing=north,half={half},hinge={hinge},open=false,powered=false]")
  +    for x in (6, 23):
  +        lancet(x, 3, 5, 7, 10, width=3)
  +
  +    # Three deep pointed arcade openings; clear space is carved through
  +    # the full two-block wall thickness, leaving a sheltered walkable porch.
  +    box(2, 27, 2, 9, 2, 3, white)
  +    box(2, 3, 2, 9, 4, 9, white)
  +    box(26, 27, 2, 9, 4, 9, white)
  +    arches = ((4, 9, 5, 8), (11, 18, 6, 9), (20, 25, 5, 8))
  +    for lo, hi, spring, tip in arches:
  +        for y in range(2, tip + 1):
  +            inset = max(0, y - spring)
  +            for x in range(lo + inset, hi - inset + 1):
  +                for z in (2, 3):
  +                    erase(x, y, z)
  +            if y > spring:
  +                put(lo + inset - 1, y, 2, stair("quartz", "east", "top"))
  +                put(hi - inset + 1, y, 2, stair("quartz", "west", "top"))
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 2, 6, 2, 2, "quartz_pillar[axis=y]")
  +        put(x, 2, 1, stone)
  +        put(x, 6, 1, stair("quartz", "south", "top"))
  +    for plane in (2, 3, 26, 27):
  +        lancet(7, 2, 4, 7, plane, axis="x", width=3, glass=False)
  +    box(2, 27, 9, 9, 4, 9, "birch_planks")
  +    for x in (6, 23):
  +        put(x, 8, 6, "lantern[hanging=true,waterlogged=false]")
  +
  +    # Front upper storey, projecting cornices, pilasters and rose tracery.
  +    box(2, 27, 10, 16, 2, 3, white)
  +    box(2, 3, 10, 16, 4, 10, white)
  +    box(26, 27, 10, 16, 4, 10, white)
  +    box(1, 28, 9, 9, 1, 3, stone)
  +    box(1, 28, 16, 16, 1, 3, stone)
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 10, 15, 1, 1, "quartz_pillar[axis=y]")
  +    for x in (6, 23):
  +        for z in (2, 3):
  +            lancet(x, 10, 13, 15, z)
  +    for x in range(10, 20):
  +        for y in range(9, 17):
  +            dx, dy = x - 14.5, y - 12.5
  +            distance = math.hypot(dx, dy)
  +            if distance <= 3.8:
  +                material = stone
  +                if distance < 3.15:
  +                    material = "gray_stained_glass"
  +                    for n in range(6):
  +                        angle = n * math.tau / 6 + math.pi / 2
  +                        if math.hypot(dx - 2 * math.cos(angle),
  +                                      dy - 2 * math.sin(angle)) < 1.12:
  +                            material = ("red_stained_glass" if n % 2 == 0
  +                                        else "purple_stained_glass")
  +                    if distance < 1:
  +                        material = "magenta_stained_glass"
  +                for z in (2, 3):
  +                    put(x, y, z, material)
  +    # Small round lights above the outer arcade openings.
  +    for x in (5, 8, 21, 24):
  +        for z in (2, 3):
  +            put(x, 8, z, "cyan_stained_glass")
  +    box(1, 28, 17, 17, 1, 10, stone)
  +    box(2, 27, 18, 18, 2, 3, white)
  +    for x in range(3, 28, 2):
  +        put(x, 18, 1, stair("quartz", "south", "top"))
  +    box(1, 28, 19, 19, 1, 3, slab("smooth_quartz"))
  +
  +    # Four rhythmic nave bays: tall lancets, paired round clerestory lights,
  +    # square buttresses and continuous white eave moldings.
  +    for z in (15, 23, 31, 39):
  +        lancet(z, 3, 8, 10, 3, axis="x", width=3)
  +        for off in (-2, 2):
  +            quatrefoil(z + off, 12, 3, axis="x")
  +        lancet(z, 9, 11, 12, 26, axis="x", width=3)
  +    for z in (11, 19, 27, 35, 42):
  +        for x in (2, 27):
  +            box(x, x, 2, 12, z, z, white)
  +            put(x, 13, z, stair("quartz", "east" if x == 2 else "west"))
  +    for x in (2, 3, 26, 27):
  +        box(x, x, 13, 13, 10, 43, stone)
  +    for z in range(12, 43, 2):
  +        put(2, 12, z, stair("quartz", "east", "top"))
  +        put(27, 12, z, stair("quartz", "west", "top"))
  +
  +    # The tiled gable uses stair courses facing uphill.  Intermediate
  +    # horizontal courses allow the broad roof's 2:3 pitch at this scale.
  +    def roof_height(x):
  +        return 14 + (min(x - 2, 27 - x) * 2) // 3
  +
  +    for x in range(2, 28):
  +        h = roof_height(x)
  +        for z in range(9, 44):
  +            put(x, h - 1, z, "red_terracotta")
  +            uphill = x + 1 if x < 14 else x - 1
  +            rising = roof_height(uphill) > h
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if rising else "bricks")
  +        for z in (10, 42):
  +            if 3 <= x <= 26:
  +                box(x, x, 14, h - 1, z, z, white)
  +    box(14, 15, 23, 23, 9, 43, slab("brick"))
  +    for z in (9, 43):
  +        for x in range(2, 28):
  +            put(x, roof_height(x) - 1, z, stone)
  +
  +    # Low lean-to aisle along the east side; its roof intersects the nave
  +    # wall, and its outer windows remain below the tiled roof.
  +    box(28, 28, 2, 7, 11, 40, white)
  +    box(26, 28, 2, 9, 11, 11, white)
  +    box(26, 28, 2, 9, 40, 40, white)
  +    for z in (16, 24, 32, 37):
  +        lancet(z, 3, 5, 6, 28, axis="x", width=1)
  +    for x in range(26, 30):
  +        h = 10 - (x - 26)
  +        for z in range(10, 42):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "west"))
  +    # Clear access from the nave into the narrow aisle.
  +    for z in (20, 21):
  +        for y in (2, 3, 4):
  +            erase(26, y, z)
  +
  +    # Rear sacristy, with a smaller complete red gable and an open interior
  +    # connection to the chancel.
  +    box(8, 8, 2, 7, 42, 46, white)
  +    box(21, 21, 2, 7, 42, 46, white)
  +    box(8, 21, 2, 7, 46, 46, white)
  +    lancet(14, 3, 5, 7, 46, width=3)
  +    for x in range(7, 23):
  +        h = 8 + min(x - 7, 22 - x) // 2
  +        for z in range(42, 47):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if min(x - 7, 22 - x) % 2 else "bricks")
  +        if 8 <= x <= 21:
  +            box(x, x, 8, h - 1, 46, 46, white)
  +    for x in (14, 15):
  +        for z in range(42, 47):
  +            put(x, 12, z, slab("brick"))
  +    for x in range(13, 17):
  +        for y in range(2, 5):
  +            erase(x, y, 42)
  +
  +    # Twin square belfries.  Solid louver blocks close each opening, with
  +    # thin horizontal dark-oak slats on the exposed face.
  +    for cx in (6, 23):
  +        lo, hi = cx - 3, cx + 3
  +        box(lo, hi, 18, 18, 3, 9, stone)
  +        for y in range(19, 23):
  +            for x in range(lo, hi + 1):
  +                for z in range(3, 10):
  +                    if x in (lo, hi) or z in (3, 9):
  +                        put(x, y, z, white)
  +        for plane in (3, 9):
  +            lancet(cx, 19, 20, 22, plane, width=3, dark=True)
  +        for plane in (lo, hi):
  +            lancet(6, 19, 20, 22, plane, axis="x", width=3, dark=True)
  +        for y in (19, 20, 21):
  +            put(cx, y, 2, slab("dark_oak", "top"))
  +        box(lo - 1, hi + 1, 23, 23, 2, 10, stone)
  +        # Seven-block tall pyramids: vertical courses alternate with
  +        # inward steps; inner-corner stair states close the four hips.
  +        radii = (3, 3, 2, 2, 1, 1, 0)
  +        for y, r in enumerate(radii, 24):
  +            box(cx - r, cx + r, y, y, 6 - r, 6 + r, "polished_deepslate")
  +            if r:
  +                for d in range(-r + 1, r):
  +                    put(cx + d, y, 6 - r, stair("polished_deepslate", "south"))
  +                    put(cx + d, y, 6 + r, stair("polished_deepslate", "north"))
  +                    put(cx - r, y, 6 + d, stair("polished_deepslate", "east"))
  +                    put(cx + r, y, 6 + d, stair("polished_deepslate", "west"))
  +                for dx, dz, facing, shape in (
  +                    (-r, -r, "south", "inner_left"),
  +                    (r, -r, "south", "inner_right"),
  +                    (-r, r, "north", "inner_right"),
  +                    (r, r, "north", "inner_left"),
  +                ):
  +                    put(cx + dx, y, 6 + dz, stair("polished_deepslate", facing, shape=shape))
  +        # Four white pinnacles rise directly from each tower's cornice.
  +        for x in (lo - 1, hi + 1):
  +            for z in (2, 10):
  +                put(x, 24, z, stone)
  +                put(x, 25, z,
  +                    "diorite_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
  +        for y in range(31, 34):
  +            connections = "east=true,north=false,south=false,west=true" if y == 32 else "east=false,north=false,south=false,west=false"
  +            put(cx, y, 6, f"iron_bars[{connections},waterlogged=false]")
  +        put(cx - 1, 32, 6, "iron_bars[east=true,north=false,south=false,west=false,waterlogged=false]")
  +        put(cx + 1, 32, 6, "iron_bars[east=false,north=false,south=false,west=true,waterlogged=false]")
  +
  +    # Simple sanctuary: central aisle, paired banks of pews, altar and
  +    # exposed transverse timber ties attached to the nave walls.
  +    box(13, 16, 2, 2, 11, 36, "red_carpet")
  +    for z in range(15, 34, 4):
  +        for lo, hi in ((6, 11), (18, 23)):
  +            box(lo, hi, 2, 2, z, z, stair("dark_oak", "north"))
  +            put(lo, 2, z - 1, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
  +            put(hi, 2, z - 1, "dark_oak_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
  +    box(8, 21, 2, 2, 37, 41, "smooth_quartz")
  +    box(12, 17, 3, 3, 39, 40, "quartz_bricks")
  +    box(12, 17, 4, 4, 39, 40, slab("smooth_quartz"))
  +    for y in range(5, 10):
  +        put(14, y, 41, "dark_oak_log[axis=y]")
  +    box(12, 16, 8, 8, 41, 41, "dark_oak_log[axis=x]")
  +    for z in (14, 22, 30, 38):
  +        box(4, 25, 13, 13, z, z, "dark_oak_log[axis=x]")
  +        for x in (10, 19):
  +            put(x, 12, z, "chain[axis=y,waterlogged=false]")
  +            put(x, 11, z, "lantern[hanging=true,waterlogged=false]")
  +
  +    assert all(0 <= x < 30 and 0 <= y < 34 and 0 <= z < 47
  +               for x, y, z in blocks)
  +    assert all(block != "air" for block in blocks.values())
  +    return blocks
  +
  +
  +if __name__ == "__main__":
  +    print(len(build()))
  
  apply patch
  patch: completed
  C:\Users\<user>\mcbuild\experiments\plain_astra\church_plain.py
  diff --git a/church_plain.py b/church_plain.py
  new file mode 100644
  index 0000000000000000000000000000000000000000..2fceee6e5f54c41d7f060687a149868f8387651b
  --- /dev/null
  +++ b/church_plain.py
  @@ -0,0 +1,304 @@
  +"""Old Catholic Shimizu Church, approximately 2 blocks per metre.
  +
  +The three-arched west front faces -Z.  Bounds: X 0..29, Y 0..33,
  +Z 0..46.  Call build() for the complete, deterministic Java block map.
  +"""
  +
  +import math
  +
  +
  +def build() -> dict[tuple[int, int, int], str]:
  +    blocks: dict[tuple[int, int, int], str] = {}
  +    white = "white_concrete"
  +    stone = "smooth_quartz"
  +
  +    def put(x, y, z, block):
  +        blocks[x, y, z] = block
  +
  +    def box(x0, x1, y0, y1, z0, z1, block):
  +        for x in range(x0, x1 + 1):
  +            for y in range(y0, y1 + 1):
  +                for z in range(z0, z1 + 1):
  +                    put(x, y, z, block)
  +
  +    def erase(x, y, z):
  +        blocks.pop((x, y, z), None)
  +
  +    def stair(material, facing, half="bottom", shape="straight"):
  +        return f"{material}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"
  +
  +    def slab(material, kind="bottom"):
  +        return f"{material}_slab[type={kind},waterlogged=false]"
  +
  +    def uv(u, y, plane, axis, block):
  +        x, z = (u, plane) if axis == "z" else (plane, u)
  +        if block is None:
  +            erase(x, y, z)
  +        else:
  +            put(x, y, z, block)
  +
  +    def lancet(center, bottom, spring, tip, plane, axis="z", width=3,
  +               glass=True, dark=False):
  +        """Pointed opening with a solid, one-voxel carved surround."""
  +        radius = width // 2
  +        for y in range(bottom - 1, tip + 2):
  +            for u in range(center - radius - 1, center + radius + 2):
  +                uv(u, y, plane, axis, stone)
  +        for y in range(bottom, tip + 1):
  +            r = radius if y <= spring else int(radius * (tip - y) / (tip - spring))
  +            for u in range(center - r, center + r + 1):
  +                if dark:
  +                    block = "dark_oak_planks"
  +                elif glass:
  +                    color = ("blue", "purple", "red", "cyan")[(y + u) % 4]
  +                    block = f"{color}_stained_glass"
  +                    if u == center and y < spring:
  +                        block = "gray_stained_glass"
  +                else:
  +                    block = None
  +                uv(u, y, plane, axis, block)
  +
  +    def quatrefoil(center, y, plane, axis="z"):
  +        for du, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
  +            uv(center + du, y + dy, plane, axis,
  +               "gray_stained_glass" if du == dy == 0 else "light_blue_stained_glass")
  +
  +    # Ground, continuous foundations, and the raised timber nave floor.
  +    box(0, 29, 0, 0, 0, 46, "grass_block")
  +    box(2, 27, 1, 1, 2, 10, "smooth_stone")
  +    box(3, 26, 1, 1, 10, 42, "stone_bricks")
  +    box(4, 25, 1, 1, 11, 41, "spruce_planks")
  +    box(26, 28, 1, 1, 11, 40, "stone_bricks")
  +    box(8, 21, 1, 1, 42, 46, "stone_bricks")
  +    box(9, 20, 1, 1, 43, 45, "spruce_planks")
  +    box(4, 25, 1, 1, 0, 0, slab("smooth_stone"))
  +    box(3, 26, 1, 1, 1, 1, stair("quartz", "south"))
  +
  +    # Nave shell and the porch's rear wall, with a working double door.
  +    box(3, 3, 2, 13, 10, 42, white)
  +    box(26, 26, 2, 13, 10, 42, white)
  +    box(3, 26, 2, 13, 42, 42, white)
  +    box(3, 26, 2, 17, 10, 10, white)
  +    lancet(14, 2, 5, 8, 10, width=5, dark=True)
  +    for x, hinge in ((14, "left"), (15, "right")):
  +        for y, half in ((2, "lower"), (3, "upper")):
  +            put(x, y, 10,
  +                f"dark_oak_door[facing=north,half={half},hinge={hinge},open=false,powered=false]")
  +    for x in (6, 23):
  +        lancet(x, 3, 5, 7, 10, width=3)
  +
  +    # Three deep pointed arcade openings; clear space is carved through
  +    # the full two-block wall thickness, leaving a sheltered walkable porch.
  +    box(2, 27, 2, 9, 2, 3, white)
  +    box(2, 3, 2, 9, 4, 9, white)
  +    box(26, 27, 2, 9, 4, 9, white)
  +    arches = ((4, 9, 5, 7), (11, 18, 5, 8), (20, 25, 5, 7))
  +    for lo, hi, spring, tip in arches:
  +        for y in range(2, tip + 1):
  +            inset = max(0, y - spring)
  +            for x in range(lo + inset, hi - inset + 1):
  +                for z in (2, 3):
  +                    erase(x, y, z)
  +            if y > spring:
  +                put(lo + inset - 1, y, 2, stair("quartz", "east", "top"))
  +                put(hi - inset + 1, y, 2, stair("quartz", "west", "top"))
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 2, 6, 2, 2, "quartz_pillar[axis=y]")
  +        put(x, 2, 1, stone)
  +        put(x, 6, 1, stair("quartz", "south", "top"))
  +    for plane in (2, 3, 26, 27):
  +        lancet(7, 2, 4, 7, plane, axis="x", width=3, glass=False)
  +    box(2, 27, 9, 9, 4, 9, "birch_planks")
  +    for x in (6, 23):
  +        put(x, 8, 6, "lantern[hanging=true,waterlogged=false]")
  +
  +    # Front upper storey, projecting cornices, pilasters and rose tracery.
  +    box(2, 27, 10, 16, 2, 3, white)
  +    box(2, 3, 10, 16, 4, 10, white)
  +    box(26, 27, 10, 16, 4, 10, white)
  +    box(1, 28, 9, 9, 1, 3, stone)
  +    box(1, 28, 16, 16, 1, 3, stone)
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 10, 15, 1, 1, "quartz_pillar[axis=y]")
  +    for x in (6, 23):
  +        for z in (2, 3):
  +            lancet(x, 10, 13, 15, z)
  +    for x in range(10, 20):
  +        for y in range(9, 17):
  +            dx, dy = x - 14.5, y - 12.5
  +            distance = math.hypot(dx, dy)
  +            if distance <= 3.8:
  +                material = stone
  +                if distance < 3.15:
  +                    material = "gray_stained_glass"
  +                    for n in range(6):
  +                        angle = n * math.tau / 6 + math.pi / 2
  +                        if math.hypot(dx - 2 * math.cos(angle),
  +                                      dy - 2 * math.sin(angle)) < 1.12:
  +                            material = ("red_stained_glass" if n % 2 == 0
  +                                        else "purple_stained_glass")
  +                    if distance < 1:
  +                        material = "magenta_stained_glass"
  +                for z in (2, 3):
  +                    put(x, y, z, material)
  +    # Small round lights above the outer arcade openings.
  +    for x in (5, 8, 21, 24):
  +        for z in (2, 3):
  +            put(x, 8, z, "cyan_stained_glass")
  +    box(1, 28, 17, 17, 1, 10, stone)
  +    box(2, 27, 18, 18, 2, 3, white)
  +    for x in range(3, 28, 2):
  +        put(x, 18, 1, stair("quartz", "south", "top"))
  +    box(1, 28, 19, 19, 1, 3, slab("smooth_quartz"))
  +
  +    # Four rhythmic nave bays: tall lancets, paired round clerestory lights,
  +    # square buttresses and continuous white eave moldings.
  +    for z in (15, 23, 31, 39):
  +        lancet(z, 3, 8, 10, 3, axis="x", width=3)
  +        for off in (-2, 2):
  +            quatrefoil(z + off, 12, 3, axis="x")
  +        lancet(z, 9, 11, 12, 26, axis="x", width=3)
  +    for z in (11, 19, 27, 35, 42):
  +        for x in (2, 27):
  +            box(x, x, 2, 12, z, z, white)
  +            put(x, 13, z, stair("quartz", "east" if x == 2 else "west"))
  +    for x in (2, 3, 26, 27):
  +        box(x, x, 13, 13, 10, 43, stone)
  +    for z in range(12, 43, 2):
  +        put(2, 12, z, stair("quartz", "east", "top"))
  +        put(27, 12, z, stair("quartz", "west", "top"))
  +
  +    # The tiled gable uses stair courses facing uphill.  Intermediate
  +    # horizontal courses allow the broad roof's 2:3 pitch at this scale.
  +    def roof_height(x):
  +        return 14 + (min(x - 2, 27 - x) * 2) // 3
  +
  +    for x in range(2, 28):
  +        h = roof_height(x)
  +        for z in range(9, 44):
  +            put(x, h - 1, z, "red_terracotta")
  +            uphill = x + 1 if x < 14 else x - 1
  +            rising = roof_height(uphill) > h
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if rising else "bricks")
  +        for z in (10, 42):
  +            if 3 <= x <= 26:
  +                box(x, x, 14, h - 1, z, z, white)
  +    box(14, 15, 23, 23, 9, 43, slab("brick"))
  +    for z in (9, 43):
  +        for x in range(2, 28):
  +            put(x, roof_height(x) - 1, z, stone)
  +
  +    # Low lean-to aisle along the east side; its roof intersects the nave
  +    # wall, and its outer windows remain below the tiled roof.
  +    box(28, 28, 2, 7, 11, 40, white)
  +    box(26, 28, 2, 9, 11, 11, white)
  +    box(26, 28, 2, 9, 40, 40, white)
  +    for z in (16, 24, 32, 37):
  +        lancet(z, 3, 5, 6, 28, axis="x", width=1)
  +    for x in range(26, 30):
  +        h = 10 - (x - 26)
  +        for z in range(10, 42):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "west"))
  +    # Clear access from the nave into the narrow aisle.
  +    for z in (20, 21):
  +        for y in (2, 3, 4):
  +            erase(26, y, z)
  +
  +    # Rear sacristy, with a smaller complete red gable and an open interior
  +    # connection to the chancel.
  +    box(8, 8, 2, 7, 42, 46, white)
  +    box(21, 21, 2, 7, 42, 46, white)
  +    box(8, 21, 2, 7, 46, 46, white)
  +    lancet(14, 3, 5, 7, 46, width=3)
  +    for x in range(7, 23):
  +        h = 8 + min(x - 7, 22 - x) // 2
  +        for z in range(42, 47):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if min(x - 7, 22 - x) % 2 else "bricks")
  +        if 8 <= x <= 21:
  +            box(x, x, 8, h - 1, 46, 46, white)
  +    for x in (14, 15):
  +        for z in range(42, 47):
  +            put(x, 12, z, slab("brick"))
  +    for x in range(13, 17):
  +        for y in range(2, 5):
  +            erase(x, y, 42)
  +
  +    # Twin square belfries.  Solid louver blocks close each opening, with
  +    # thin horizontal dark-oak slats on the exposed face.
  +    for cx in (6, 23):
  +        lo, hi = cx - 3, cx + 3
  +        box(lo, hi, 18, 18, 3, 9, stone)
  +        for y in range(19, 23):
  +            for x in range(lo, hi + 1):
  +                for z in range(3, 10):
  +                    if x in (lo, hi) or z in (3, 9):
  +                        put(x, y, z, white)
  +        for plane in (3, 9):
  +            lancet(cx, 19, 20, 22, plane, width=3, dark=True)
  +        for plane in (lo, hi):
  +            lancet(6, 19, 20, 22, plane, axis="x", width=3, dark=True)
  +        for y in (19, 20, 21):
  +            put(cx, y, 2, slab("dark_oak", "top"))
  +        box(lo - 1, hi + 1, 23, 23, 2, 10, stone)
  +        # Seven-block tall pyramids: vertical courses alternate with
  +        # inward steps; inner-corner stair states close the four hips.
  +        radii = (3, 3, 2, 2, 1, 1, 0)
  +        for y, r in enumerate(radii, 24):
  +            box(cx - r, cx + r, y, y, 6 - r, 6 + r, "polished_deepslate")
  +            if r:
  +                for d in range(-r + 1, r):
  +                    put(cx + d, y, 6 - r, stair("polished_deepslate", "south"))
  +                    put(cx + d, y, 6 + r, stair("polished_deepslate", "north"))
  +                    put(cx - r, y, 6 + d, stair("polished_deepslate", "east"))
  +                    put(cx + r, y, 6 + d, stair("polished_deepslate", "west"))
  +                for dx, dz, facing, shape in (
  +                    (-r, -r, "south", "inner_left"),
  +                    (r, -r, "south", "inner_right"),
  +                    (-r, r, "north", "inner_right"),
  +                    (r, r, "north", "inner_left"),
  +                ):
  +                    put(cx + dx, y, 6 + dz, stair("polished_deepslate", facing, shape=shape))
  +        # Four white pinnacles rise directly from each tower's cornice.
  +        for x in (lo - 1, hi + 1):
  +            for z in (2, 10):
  +                put(x, 24, z, stone)
  +                put(x, 25, z,
  +                    "diorite_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
  +        for y in range(31, 34):
  +            connections = "east=true,north=false,south=false,west=true" if y == 32 else "east=false,north=false,south=false,west=false"
  +            put(cx, y, 6, f"iron_bars[{connections},waterlogged=false]")
  +        put(cx - 1, 32, 6, "iron_bars[east=true,north=false,south=false,west=false,waterlogged=false]")
  +        put(cx + 1, 32, 6, "iron_bars[east=false,north=false,south=false,west=true,waterlogged=false]")
  +
  +    # Simple sanctuary: central aisle, paired banks of pews, altar and
  +    # exposed transverse timber ties attached to the nave walls.
  +    box(13, 16, 2, 2, 11, 36, "red_carpet")
  +    for z in range(15, 34, 4):
  +        for lo, hi in ((6, 11), (18, 23)):
  +            box(lo, hi, 2, 2, z, z, stair("dark_oak", "north"))
  +            put(lo, 2, z - 1, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
  +            put(hi, 2, z - 1, "dark_oak_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
  +    box(8, 21, 2, 2, 37, 41, "smooth_quartz")
  +    box(12, 17, 3, 3, 39, 40, "quartz_bricks")
  +    box(12, 17, 4, 4, 39, 40, slab("smooth_quartz"))
  +    for y in range(5, 10):
  +        put(14, y, 41, "dark_oak_log[axis=y]")
  +    box(12, 16, 8, 8, 41, 41, "dark_oak_log[axis=x]")
  +    for z in (14, 22, 30, 38):
  +        box(4, 25, 13, 13, z, z, "dark_oak_log[axis=x]")
  +        for x in (10, 19):
  +            put(x, 12, z, "chain[axis=y,waterlogged=false]")
  +            put(x, 11, z, "lantern[hanging=true,waterlogged=false]")
  +
  +    assert all(0 <= x < 30 and 0 <= y < 34 and 0 <= z < 47
  +               for x, y, z in blocks)
  +    assert all(block != "air" for block in blocks.values())
  +    return blocks
  +
  +
  +if __name__ == "__main__":
  +    print(len(build()))
- The file is written. Python isn’t on this shell’s PATH, so I’m locating an installed interpreter to run the required check.
- [church_plain.py](church_plain.py)
  diff --git a/church_plain.py b/church_plain.py
  new file mode 100644
  index 0000000000000000000000000000000000000000..2fceee6e5f54c41d7f060687a149868f8387651b
  --- /dev/null
  +++ b/church_plain.py
  @@ -0,0 +1,304 @@
  +"""Old Catholic Shimizu Church, approximately 2 blocks per metre.
  +
  +The three-arched west front faces -Z.  Bounds: X 0..29, Y 0..33,
  +Z 0..46.  Call build() for the complete, deterministic Java block map.
  +"""
  +
  +import math
  +
  +
  +def build() -> dict[tuple[int, int, int], str]:
  +    blocks: dict[tuple[int, int, int], str] = {}
  +    white = "white_concrete"
  +    stone = "smooth_quartz"
  +
  +    def put(x, y, z, block):
  +        blocks[x, y, z] = block
  +
  +    def box(x0, x1, y0, y1, z0, z1, block):
  +        for x in range(x0, x1 + 1):
  +            for y in range(y0, y1 + 1):
  +                for z in range(z0, z1 + 1):
  +                    put(x, y, z, block)
  +
  +    def erase(x, y, z):
  +        blocks.pop((x, y, z), None)
  +
  +    def stair(material, facing, half="bottom", shape="straight"):
  +        return f"{material}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"
  +
  +    def slab(material, kind="bottom"):
  +        return f"{material}_slab[type={kind},waterlogged=false]"
  +
  +    def uv(u, y, plane, axis, block):
  +        x, z = (u, plane) if axis == "z" else (plane, u)
  +        if block is None:
  +            erase(x, y, z)
  +        else:
  +            put(x, y, z, block)
  +
  +    def lancet(center, bottom, spring, tip, plane, axis="z", width=3,
  +               glass=True, dark=False):
  +        """Pointed opening with a solid, one-voxel carved surround."""
  +        radius = width // 2
  +        for y in range(bottom - 1, tip + 2):
  +            for u in range(center - radius - 1, center + radius + 2):
  +                uv(u, y, plane, axis, stone)
  +        for y in range(bottom, tip + 1):
  +            r = radius if y <= spring else int(radius * (tip - y) / (tip - spring))
  +            for u in range(center - r, center + r + 1):
  +                if dark:
  +                    block = "dark_oak_planks"
  +                elif glass:
  +                    color = ("blue", "purple", "red", "cyan")[(y + u) % 4]
  +                    block = f"{color}_stained_glass"
  +                    if u == center and y < spring:
  +                        block = "gray_stained_glass"
  +                else:
  +                    block = None
  +                uv(u, y, plane, axis, block)
  +
  +    def quatrefoil(center, y, plane, axis="z"):
  +        for du, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
  +            uv(center + du, y + dy, plane, axis,
  +               "gray_stained_glass" if du == dy == 0 else "light_blue_stained_glass")
  +
  +    # Ground, continuous foundations, and the raised timber nave floor.
  +    box(0, 29, 0, 0, 0, 46, "grass_block")
  +    box(2, 27, 1, 1, 2, 10, "smooth_stone")
  +    box(3, 26, 1, 1, 10, 42, "stone_bricks")
  +    box(4, 25, 1, 1, 11, 41, "spruce_planks")
  +    box(26, 28, 1, 1, 11, 40, "stone_bricks")
  +    box(8, 21, 1, 1, 42, 46, "stone_bricks")
  +    box(9, 20, 1, 1, 43, 45, "spruce_planks")
  +    box(4, 25, 1, 1, 0, 0, slab("smooth_stone"))
  +    box(3, 26, 1, 1, 1, 1, stair("quartz", "south"))
  +
  +    # Nave shell and the porch's rear wall, with a working double door.
  +    box(3, 3, 2, 13, 10, 42, white)
  +    box(26, 26, 2, 13, 10, 42, white)
  +    box(3, 26, 2, 13, 42, 42, white)
  +    box(3, 26, 2, 17, 10, 10, white)
  +    lancet(14, 2, 5, 8, 10, width=5, dark=True)
  +    for x, hinge in ((14, "left"), (15, "right")):
  +        for y, half in ((2, "lower"), (3, "upper")):
  +            put(x, y, 10,
  +                f"dark_oak_door[facing=north,half={half},hinge={hinge},open=false,powered=false]")
  +    for x in (6, 23):
  +        lancet(x, 3, 5, 7, 10, width=3)
  +
  +    # Three deep pointed arcade openings; clear space is carved through
  +    # the full two-block wall thickness, leaving a sheltered walkable porch.
  +    box(2, 27, 2, 9, 2, 3, white)
  +    box(2, 3, 2, 9, 4, 9, white)
  +    box(26, 27, 2, 9, 4, 9, white)
  +    arches = ((4, 9, 5, 7), (11, 18, 5, 8), (20, 25, 5, 7))
  +    for lo, hi, spring, tip in arches:
  +        for y in range(2, tip + 1):
  +            inset = max(0, y - spring)
  +            for x in range(lo + inset, hi - inset + 1):
  +                for z in (2, 3):
  +                    erase(x, y, z)
  +            if y > spring:
  +                put(lo + inset - 1, y, 2, stair("quartz", "east", "top"))
  +                put(hi - inset + 1, y, 2, stair("quartz", "west", "top"))
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 2, 6, 2, 2, "quartz_pillar[axis=y]")
  +        put(x, 2, 1, stone)
  +        put(x, 6, 1, stair("quartz", "south", "top"))
  +    for plane in (2, 3, 26, 27):
  +        lancet(7, 2, 4, 7, plane, axis="x", width=3, glass=False)
  +    box(2, 27, 9, 9, 4, 9, "birch_planks")
  +    for x in (6, 23):
  +        put(x, 8, 6, "lantern[hanging=true,waterlogged=false]")
  +
  +    # Front upper storey, projecting cornices, pilasters and rose tracery.
  +    box(2, 27, 10, 16, 2, 3, white)
  +    box(2, 3, 10, 16, 4, 10, white)
  +    box(26, 27, 10, 16, 4, 10, white)
  +    box(1, 28, 9, 9, 1, 3, stone)
  +    box(1, 28, 16, 16, 1, 3, stone)
  +    for x in (3, 10, 19, 26):
  +        box(x, x, 10, 15, 1, 1, "quartz_pillar[axis=y]")
  +    for x in (6, 23):
  +        for z in (2, 3):
  +            lancet(x, 10, 13, 15, z)
  +    for x in range(10, 20):
  +        for y in range(9, 17):
  +            dx, dy = x - 14.5, y - 12.5
  +            distance = math.hypot(dx, dy)
  +            if distance <= 3.8:
  +                material = stone
  +                if distance < 3.15:
  +                    material = "gray_stained_glass"
  +                    for n in range(6):
  +                        angle = n * math.tau / 6 + math.pi / 2
  +                        if math.hypot(dx - 2 * math.cos(angle),
  +                                      dy - 2 * math.sin(angle)) < 1.12:
  +                            material = ("red_stained_glass" if n % 2 == 0
  +                                        else "purple_stained_glass")
  +                    if distance < 1:
  +                        material = "magenta_stained_glass"
  +                for z in (2, 3):
  +                    put(x, y, z, material)
  +    # Small round lights above the outer arcade openings.
  +    for x in (5, 8, 21, 24):
  +        for z in (2, 3):
  +            put(x, 8, z, "cyan_stained_glass")
  +    box(1, 28, 17, 17, 1, 10, stone)
  +    box(2, 27, 18, 18, 2, 3, white)
  +    for x in range(3, 28, 2):
  +        put(x, 18, 1, stair("quartz", "south", "top"))
  +    box(1, 28, 19, 19, 1, 3, slab("smooth_quartz"))
  +
  +    # Four rhythmic nave bays: tall lancets, paired round clerestory lights,
  +    # square buttresses and continuous white eave moldings.
  +    for z in (15, 23, 31, 39):
  +        lancet(z, 3, 8, 10, 3, axis="x", width=3)
  +        for off in (-2, 2):
  +            quatrefoil(z + off, 12, 3, axis="x")
  +        lancet(z, 9, 11, 12, 26, axis="x", width=3)
  +    for z in (11, 19, 27, 35, 42):
  +        for x in (2, 27):
  +            box(x, x, 2, 12, z, z, white)
  +            put(x, 13, z, stair("quartz", "east" if x == 2 else "west"))
  +    for x in (2, 3, 26, 27):
  +        box(x, x, 13, 13, 10, 43, stone)
  +    for z in range(12, 43, 2):
  +        put(2, 12, z, stair("quartz", "east", "top"))
  +        put(27, 12, z, stair("quartz", "west", "top"))
  +
  +    # The tiled gable uses stair courses facing uphill.  Intermediate
  +    # horizontal courses allow the broad roof's 2:3 pitch at this scale.
  +    def roof_height(x):
  +        return 14 + (min(x - 2, 27 - x) * 2) // 3
  +
  +    for x in range(2, 28):
  +        h = roof_height(x)
  +        for z in range(9, 44):
  +            put(x, h - 1, z, "red_terracotta")
  +            uphill = x + 1 if x < 14 else x - 1
  +            rising = roof_height(uphill) > h
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if rising else "bricks")
  +        for z in (10, 42):
  +            if 3 <= x <= 26:
  +                box(x, x, 14, h - 1, z, z, white)
  +    box(14, 15, 23, 23, 9, 43, slab("brick"))
  +    for z in (9, 43):
  +        for x in range(2, 28):
  +            put(x, roof_height(x) - 1, z, stone)
  +
  +    # Low lean-to aisle along the east side; its roof intersects the nave
  +    # wall, and its outer windows remain below the tiled roof.
  +    box(28, 28, 2, 7, 11, 40, white)
  +    box(26, 28, 2, 9, 11, 11, white)
  +    box(26, 28, 2, 9, 40, 40, white)
  +    for z in (16, 24, 32, 37):
  +        lancet(z, 3, 5, 6, 28, axis="x", width=1)
  +    for x in range(26, 30):
  +        h = 10 - (x - 26)
  +        for z in range(10, 42):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "west"))
  +    # Clear access from the nave into the narrow aisle.
  +    for z in (20, 21):
  +        for y in (2, 3, 4):
  +            erase(26, y, z)
  +
  +    # Rear sacristy, with a smaller complete red gable and an open interior
  +    # connection to the chancel.
  +    box(8, 8, 2, 7, 42, 46, white)
  +    box(21, 21, 2, 7, 42, 46, white)
  +    box(8, 21, 2, 7, 46, 46, white)
  +    lancet(14, 3, 5, 7, 46, width=3)
  +    for x in range(7, 23):
  +        h = 8 + min(x - 7, 22 - x) // 2
  +        for z in range(42, 47):
  +            put(x, h - 1, z, "red_terracotta")
  +            put(x, h, z, stair("brick", "east" if x < 15 else "west")
  +                if min(x - 7, 22 - x) % 2 else "bricks")
  +        if 8 <= x <= 21:
  +            box(x, x, 8, h - 1, 46, 46, white)
  +    for x in (14, 15):
  +        for z in range(42, 47):
  +            put(x, 12, z, slab("brick"))
  +    for x in range(13, 17):
  +        for y in range(2, 5):
  +            erase(x, y, 42)
  +
  +    # Twin square belfries.  Solid louver blocks close each opening, with
  +    # thin horizontal dark-oak slats on the exposed face.
  +    for cx in (6, 23):
  +        lo, hi = cx - 3, cx + 3
  +        box(lo, hi, 18, 18, 3, 9, stone)
  +        for y in range(19, 23):
  +            for x in range(lo, hi + 1):
  +                for z in range(3, 10):
  +                    if x in (lo, hi) or z in (3, 9):
  +                        put(x, y, z, white)
  +        for plane in (3, 9):
  +            lancet(cx, 19, 20, 22, plane, width=3, dark=True)
  +        for plane in (lo, hi):
  +            lancet(6, 19, 20, 22, plane, axis="x", width=3, dark=True)
  +        for y in (19, 20, 21):
  +            put(cx, y, 2, slab("dark_oak", "top"))
  +        box(lo - 1, hi + 1, 23, 23, 2, 10, stone)
  +        # Seven-block tall pyramids: vertical courses alternate with
  +        # inward steps; inner-corner stair states close the four hips.
  +        radii = (3, 3, 2, 2, 1, 1, 0)
  +        for y, r in enumerate(radii, 24):
  +            box(cx - r, cx + r, y, y, 6 - r, 6 + r, "polished_deepslate")
  +            if r:
  +                for d in range(-r + 1, r):
  +                    put(cx + d, y, 6 - r, stair("polished_deepslate", "south"))
  +                    put(cx + d, y, 6 + r, stair("polished_deepslate", "north"))
  +                    put(cx - r, y, 6 + d, stair("polished_deepslate", "east"))
  +                    put(cx + r, y, 6 + d, stair("polished_deepslate", "west"))
  +                for dx, dz, facing, shape in (
  +                    (-r, -r, "south", "inner_left"),
  +                    (r, -r, "south", "inner_right"),
  +                    (-r, r, "north", "inner_right"),
  +                    (r, r, "north", "inner_left"),
  +                ):
  +                    put(cx + dx, y, 6 + dz, stair("polished_deepslate", facing, shape=shape))
  +        # Four white pinnacles rise directly from each tower's cornice.
  +        for x in (lo - 1, hi + 1):
  +            for z in (2, 10):
  +                put(x, 24, z, stone)
  +                put(x, 25, z,
  +                    "diorite_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
  +        for y in range(31, 34):
  +            connections = "east=true,north=false,south=false,west=true" if y == 32 else "east=false,north=false,south=false,west=false"
  +            put(cx, y, 6, f"iron_bars[{connections},waterlogged=false]")
  +        put(cx - 1, 32, 6, "iron_bars[east=true,north=false,south=false,west=false,waterlogged=false]")
  +        put(cx + 1, 32, 6, "iron_bars[east=false,north=false,south=false,west=true,waterlogged=false]")
  +
  +    # Simple sanctuary: central aisle, paired banks of pews, altar and
  +    # exposed transverse timber ties attached to the nave walls.
  +    box(13, 16, 2, 2, 11, 36, "red_carpet")
  +    for z in range(15, 34, 4):
  +        for lo, hi in ((6, 11), (18, 23)):
  +            box(lo, hi, 2, 2, z, z, stair("dark_oak", "north"))
  +            put(lo, 2, z - 1, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
  +            put(hi, 2, z - 1, "dark_oak_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
  +    box(8, 21, 2, 2, 37, 41, "smooth_quartz")
  +    box(12, 17, 3, 3, 39, 40, "quartz_bricks")
  +    box(12, 17, 4, 4, 39, 40, slab("smooth_quartz"))
  +    for y in range(5, 10):
  +        put(14, y, 41, "dark_oak_log[axis=y]")
  +    box(12, 16, 8, 8, 41, 41, "dark_oak_log[axis=x]")
  +    for z in (14, 22, 30, 38):
  +        box(4, 25, 13, 13, z, z, "dark_oak_log[axis=x]")
  +        for x in (10, 19):
  +            put(x, 12, z, "chain[axis=y,waterlogged=false]")
  +            put(x, 11, z, "lantern[hanging=true,waterlogged=false]")
  +
  +    assert all(0 <= x < 30 and 0 <= y < 34 and 0 <= z < 47
  +               for x, y, z in blocks)
  +    assert all(block != "air" for block in blocks.values())
  +    return blocks
  +
  +
  +if __name__ == "__main__":
  +    print(len(build()))
  
  tokens used
  32,233
  [church_plain.py](church_plain.py)
  
  real	7m6.185s
  user	0m0.015s
  sys	0m0.000s
