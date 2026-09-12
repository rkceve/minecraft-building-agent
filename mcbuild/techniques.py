"""Coded placement patterns read from the reference cathedral (relative coordinates).

Every function is pure: it takes geometry + a `Palette` and returns a new `Voxels` dict of
the blocks to place. The caller (`mcbuild.dsl.Build`) merges these in call order (later
calls win) and tags provenance. The special string value `"air"` in a returned dict means
"delete this voxel" at merge time -- it is not a real block id.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from . import blockstate as bs
from .litematic import Voxels
from .palette import Palette, variant

__all__ = [
    "Frame",
    "wall_fill",
    "corner_pillar",
    "pilaster",
    "wall_depth",
    "window_frame",
    "eave",
    "gable_roof",
    "floor_texture",
    "buttress",
    "spire",
    "door_opening",
    "plinth",
    "beam",
]

AIR = "air"

_FACE_NORMAL = {"n": (0, 0, -1), "s": (0, 0, 1), "e": (1, 0, 0), "w": (-1, 0, 0)}
_FACE_UVEC = {"n": (-1, 0, 0), "s": (1, 0, 0), "e": (0, 0, -1), "w": (0, 0, 1)}
_FACE_TO_FACING = {"n": "north", "s": "south", "e": "east", "w": "west"}
_FACE_TURNS = {"s": 0, "w": 1, "n": 2, "e": 3}


def _facing_word(face: str) -> str:
    return _FACE_TO_FACING[face]


@dataclass(frozen=True)
class Frame:
    """Coordinate frame for a face-attached wall.

    `u` runs along the face left-to-right as seen from outside, `v` runs up, `d` is depth
    (0 = wall plane, +1 = one block outward, -1 = one block inward). `thickness` is the
    wall's own thickness (used by openings to cut all the way through).
    """

    face: str
    x0: int
    y0: int
    z0: int
    width: int
    height: int
    thickness: int = 1

    def world(self, u: int, v: int, d: int = 0) -> tuple[int, int, int]:
        nx, ny, nz = _FACE_NORMAL[self.face]
        ux, uy, uz = _FACE_UVEC[self.face]
        return (self.x0 + u * ux + d * nx, self.y0 + v, self.z0 + u * uz + d * nz)

    @property
    def turns(self) -> int:
        """Quarter turns (CW, viewed from above) from a south-facing reference to this
        frame's outward direction."""
        return _FACE_TURNS[self.face]


# ---------------------------------------------------------------------------
# 1. wall_fill
# ---------------------------------------------------------------------------
def wall_fill(frame: Frame, pal: Palette, thickness: int = 1) -> Voxels:
    vox: Voxels = {}
    for u in range(frame.width):
        for v in range(frame.height):
            for t in range(thickness):
                vox[frame.world(u, v, -t)] = pal.primary
    return vox


# ---------------------------------------------------------------------------
# 2. corner_pillar
# ---------------------------------------------------------------------------
def corner_pillar(x: int, z: int, y0: int, height: int, pal: Palette, size: int = 3) -> Voxels:
    vox: Voxels = {}
    ring_block = bs.wall(variant(pal, "secondary", "wall"))
    cap_slab = bs.slab(variant(pal, "secondary", "slab"), "top")
    pin_wall = bs.wall(variant(pal, "accent", "wall"))
    light_up = f"{pal.light}[facing=up]"

    corners = {(0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)}
    center_i, center_k = size // 2, size // 2

    for y in range(y0, y0 + height):
        band = y >= y0 + 2 and (y - (y0 + 2)) % 6 == 0
        for i in range(size):
            for k in range(size):
                pos = (x + i, y, z + k)
                on_perimeter = i in (0, size - 1) or k in (0, size - 1)
                if band and on_perimeter:
                    vox[pos] = pal.accent
                elif (not band) and (i, k) in corners:
                    vox[pos] = ring_block
                else:
                    vox[pos] = pal.primary

    y_cap = y0 + height
    for i in range(-1, size + 1):
        for k in range(-1, size + 1):
            vox[(x + i, y_cap, z + k)] = cap_slab

    y_acc = y_cap + 1
    for i in range(size):
        for k in range(size):
            vox[(x + i, y_acc, z + k)] = pal.accent

    y_pin = y_acc + 1
    for (i, k) in corners:
        vox[(x + i, y_pin, z + k)] = light_up
    vox[(x + center_i, y_pin, z + center_k)] = pin_wall
    vox[(x + center_i, y_pin + 1, z + center_k)] = pin_wall
    vox[(x + center_i, y_pin + 2, z + center_k)] = light_up
    return vox


# ---------------------------------------------------------------------------
# 3. pilaster
# ---------------------------------------------------------------------------
def pilaster(frame: Frame, pal: Palette, u: int, width: int = 1) -> Voxels:
    vox: Voxels = {}
    top = frame.height - 1
    cap = bs.wall(variant(pal, "secondary", "wall"))
    plinth = bs.slab(variant(pal, "secondary", "slab"), "bottom")
    for w in range(width):
        uu = u + w
        for v in range(frame.height):
            vox[frame.world(uu, v, 1)] = pal.accent
        vox[frame.world(uu, top + 1, 1)] = cap
        vox[frame.world(uu, 0, 2)] = plinth
    return vox


# ---------------------------------------------------------------------------
# 4. wall_depth
# ---------------------------------------------------------------------------
def wall_depth(frame: Frame, pal: Palette, bay: int = 6) -> Voxels:
    vox: Voxels = {}
    width = frame.width
    count = max(0, width // bay)
    leftover = width - count * bay
    left_pad = leftover // 2
    cols = sorted({c for c in (left_pad + i * bay for i in range(count + 1)) if 0 <= c < width})

    for u in cols:
        vox.update(pilaster(frame, pal, u))

    for u in range(width):
        for v in (0, 1):
            if v < frame.height:
                vox[frame.world(u, v, 1)] = pal.accent

    top_slab = bs.slab(variant(pal, "secondary", "slab"), "top")
    for u in range(width):
        vox[frame.world(u, frame.height - 1, 1)] = top_slab

    for i in range(len(cols) - 1):
        if i % 2 == 1:
            u0, u1 = cols[i] + 1, cols[i + 1] - 1
            for u in range(u0, u1 + 1):
                for v in range(2, frame.height - 3 + 1):
                    if 0 <= v < frame.height:
                        vox[frame.world(u, v, 0)] = pal.secondary
    return vox


# ---------------------------------------------------------------------------
# shared pointed/round arch shape helpers
# ---------------------------------------------------------------------------
def _pointed_shape(width: int, height: int, round_style: bool = False) -> tuple[set[tuple[int, int]], int]:
    spring_h = height - ((width + 1) // 2) * 2
    if spring_h < 2:
        round_style = True
        spring_h = max(0, spring_h)
    arch_rows = height - spring_h
    max_inset = (width - 1) // 2

    opening: set[tuple[int, int]] = set()
    for r in range(spring_h):
        for uu in range(width):
            opening.add((uu, r))
    for j in range(arch_rows):
        inset = min(j if round_style else j // 2, max_inset)
        left, right = inset, width - 1 - inset
        row = spring_h + j
        for uu in range(left, right + 1):
            opening.add((uu, row))
    return opening, spring_h


def _outline_of(opening: set[tuple[int, int]]) -> set[tuple[int, int]]:
    outline: set[tuple[int, int]] = set()
    for (uu, r) in opening:
        for du, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (uu + du, r + dr)
            if n not in opening:
                outline.add(n)
    return outline


# ---------------------------------------------------------------------------
# 5. window_frame
# ---------------------------------------------------------------------------
def window_frame(
    frame: Frame,
    u: int,
    v: int,
    width: int,
    height: int,
    pal: Palette,
    style: str = "pointed",
    mullion: bool = True,
) -> Voxels:
    vox: Voxels = {}

    if style == "rose":
        return _rose_window(frame, u, v, width, pal)

    if style == "cathedral":
        from . import stamps as _stamps

        return _stamps.window_frame_cathedral(frame, u, v, width, height, thickness=frame.thickness)

    round_style = style == "round"
    opening, spring_h = _pointed_shape(width, height, round_style)
    outline = _outline_of(opening)

    # Clear the opening's interior through the relief layer (d=+1) AND the wall's
    # thickness (d<=0) -- a real reveal is open all the way through; only the outline
    # (jambs/arch) stays solid at d=+1 as a "proud" frame (see below).
    for (uu, r) in opening:
        for d in range(1, -frame.thickness, -1):
            vox[frame.world(u + uu, v + r, d)] = AIR

    for (uu, r) in outline:
        vox[frame.world(u + uu, v + r, 0)] = pal.accent
        vox[frame.world(u + uu, v + r, 1)] = pal.accent

    sill_slab = bs.slab(variant(pal, "secondary", "slab"), "top")
    sill_stair = bs.stairs_toward(variant(pal, "secondary", "stairs"), frame.face, half="top")
    for uu in range(-1, width + 1):
        vox[frame.world(u + uu, v - 1, 1)] = sill_slab
        vox[frame.world(u + uu, v - 2, 1)] = sill_stair

    glass_block = bs.pane(pal.glass)
    for (uu, r) in opening:
        vox[frame.world(u + uu, v + r, 0)] = glass_block

    if mullion and width >= 5:
        fence_block = bs.fence(variant(pal, "trim", "fence"))
        trapdoor_block = bs.trapdoor(
            variant(pal, "trim", "trapdoor"), _facing_word(frame.face), half="bottom", open=True
        )
        mu = u + width // 2
        for r in range(spring_h):
            vox[frame.world(mu, v + r, 0)] = fence_block
        for uu in range(width):
            vox[frame.world(u + uu, v + spring_h - 1, 1)] = trapdoor_block

    return vox


def _rose_window(frame: Frame, u: int, v: int, diameter: int, pal: Palette) -> Voxels:
    vox: Voxels = {}
    r = diameter / 2.0
    cu = u + (diameter - 1) / 2.0
    cv = v + (diameter - 1) / 2.0

    opening: set[tuple[int, int]] = set()
    for i in range(diameter):
        for j in range(diameter):
            du, dv = (i - (diameter - 1) / 2.0), (j - (diameter - 1) / 2.0)
            if du * du + dv * dv <= r * r:
                opening.add((i, j))

    for (uu, vv) in opening:
        for d in range(1, -frame.thickness, -1):
            vox[frame.world(u + uu, v + vv, d)] = AIR
    outline = _outline_of(opening)
    for (uu, vv) in outline:
        vox[frame.world(u + uu, v + vv, 0)] = pal.accent
        vox[frame.world(u + uu, v + vv, 1)] = variant(pal, "secondary", "wall")

    glass_block = bs.pane(pal.glass)
    for (uu, vv) in opening:
        vox[frame.world(u + uu, v + vv, 0)] = glass_block

    fence_block = bs.fence(variant(pal, "trim", "fence"))
    import math

    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        du_dir, dv_dir = math.cos(rad), math.sin(rad)
        for step in range(1, int(r) + 1):
            uu = round(cu + du_dir * step) - u
            vv = round(cv + dv_dir * step) - v
            if (uu, vv) in opening:
                vox[frame.world(u + uu, v + vv, 0)] = fence_block
    return vox


# ---------------------------------------------------------------------------
# 6. eave
# ---------------------------------------------------------------------------
def eave(frame: Frame, pal: Palette, overhang: int = 1) -> Voxels:
    vox: Voxels = {}
    top = frame.height - 1
    inv_stair = bs.stairs_toward(variant(pal, "secondary", "stairs"), frame.face, half="top")
    top_slab = bs.slab(variant(pal, "secondary", "slab"), "top")
    for uu in range(frame.width):
        vox[frame.world(uu, top, 1)] = inv_stair
        vox[frame.world(uu, top + 1, 1)] = top_slab
        if overhang >= 2:
            vox[frame.world(uu, top + 1, 2)] = top_slab
        vox[frame.world(uu, top + 1, 0)] = pal.primary
    return vox


# ---------------------------------------------------------------------------
# ridge ornament (odd-span gable_roof only)
# ---------------------------------------------------------------------------
def _ridge_ornament(pos, lo0: int, lo1: int, y: int, span: int, pal: Palette) -> Voxels:
    """Decorate the 1-block-wide ridge row of an odd-span gable roof: posts every 4th
    block from both ends (replacing the ridge slab with a short wall + light), and a
    2-tall finial at each gable end of the ridge line."""
    vox: Voxels = {}
    post_block = bs.wall(variant(pal, "secondary", "wall"))
    finial_block = bs.wall(variant(pal, "accent", "wall"))
    light_up = f"{pal.light}[facing=up]"

    post_positions: set[int] = set()
    length_total = lo1 - lo0
    i = 0
    while i <= length_total:
        post_positions.add(lo0 + i)
        post_positions.add(lo1 - i)
        i += 4
    post_positions -= {lo0, lo1}

    for length in post_positions:
        vox[pos(length, y + 1, span)] = post_block
        vox[pos(length, y + 2, span)] = light_up

    for length in (lo0, lo1):
        vox[pos(length, y + 1, span)] = finial_block
        vox[pos(length, y + 2, span)] = finial_block
        vox[pos(length, y + 3, span)] = light_up

    return vox


# ---------------------------------------------------------------------------
# 7. gable_roof
# ---------------------------------------------------------------------------
def gable_roof(
    x0: int,
    z0: int,
    x1: int,
    z1: int,
    y_base: int,
    pal: Palette,
    ridge: str = "x",
    pitch: int = 1,
    overhang: int = 1,
    gable_fill: bool = True,
) -> Voxels:
    vox: Voxels = {}
    roof_block = pal.roof
    roof_stairs_base = variant(pal, "roof", "stairs")
    roof_slab_base = variant(pal, "roof", "slab")

    if ridge == "x":
        lo0, lo1 = x0 - overhang, x1 + overhang
        s0, s1 = z0, z1
        face_a, face_b = "n", "s"

        def pos(length: int, y: int, span: int) -> tuple[int, int, int]:
            return (length, y, span)

        gable_lengths = (x0, x1)
    else:
        lo0, lo1 = z0 - overhang, z1 + overhang
        s0, s1 = x0, x1
        face_a, face_b = "w", "e"

        def pos(length: int, y: int, span: int) -> tuple[int, int, int]:
            return (span, y, length)

        gable_lengths = (z0, z1)

    k = 0
    while True:
        a = s0 - overhang + k
        b = s1 + overhang - k
        y = y_base + k * pitch
        if a > b:
            break
        if a == b:
            for length in range(lo0, lo1 + 1):
                vox[pos(length, y, a)] = roof_block
                vox[pos(length, y + 1, a)] = bs.slab(roof_slab_base, "bottom")
            vox.update(_ridge_ornament(pos, lo0, lo1, y, a, pal))
            break
        if b - a == 1:
            for length in range(lo0, lo1 + 1):
                vox[pos(length, y, a)] = bs.stairs_toward(roof_stairs_base, face_a, "bottom")
                vox[pos(length, y, b)] = bs.stairs_toward(roof_stairs_base, face_b, "bottom")
                for yy in range(y_base, y):
                    vox[pos(length, yy, a)] = roof_block
                    vox[pos(length, yy, b)] = roof_block
            break
        for length in range(lo0, lo1 + 1):
            vox[pos(length, y, a)] = bs.stairs_toward(roof_stairs_base, face_a, "bottom")
            vox[pos(length, y, b)] = bs.stairs_toward(roof_stairs_base, face_b, "bottom")
            for yy in range(y_base, y):
                vox[pos(length, yy, a)] = roof_block
                vox[pos(length, yy, b)] = roof_block
        k += 1

    # eave return: an extra inverted-stair row just under the very edge of the overhang.
    for length in range(lo0, lo1 + 1):
        vox[pos(length, y_base - 1, s0 - overhang)] = bs.stairs_toward(roof_stairs_base, face_a, "top")
        vox[pos(length, y_base - 1, s1 + overhang)] = bs.stairs_toward(roof_stairs_base, face_b, "top")

    if gable_fill:
        for length in gable_lengths:
            for span in range(s0 - overhang, s1 + overhang + 1):
                k_a = span - (s0 - overhang)
                k_b = (s1 + overhang) - span
                k2 = min(k_a, k_b)
                if k2 < 0:
                    continue
                y_top = y_base + k2 * pitch
                for yy in range(y_base, y_top):
                    vox[pos(length, yy, span)] = pal.primary

    return vox


# ---------------------------------------------------------------------------
# 8. floor_texture
# ---------------------------------------------------------------------------
def floor_texture(x0: int, z0: int, x1: int, z1: int, y: int, pal: Palette, seed: int = 0) -> Voxels:
    vox: Voxels = {}
    rng = random.Random(seed)
    double_slab = bs.slab(variant(pal, "secondary", "slab"), "double")
    for xx in range(x0, x1 + 1):
        for zz in range(z0, z1 + 1):
            if xx in (x0, x1) or zz in (z0, z1):
                vox[(xx, y, zz)] = pal.accent
            elif (xx + zz) % 2 == 0:
                vox[(xx, y, zz)] = pal.primary
            else:
                vox[(xx, y, zz)] = double_slab if rng.random() < 0.15 else pal.secondary
    return vox


# ---------------------------------------------------------------------------
# 9. buttress
# ---------------------------------------------------------------------------
def buttress(frame: Frame, pal: Palette, u: int, depth: int = 3, height: int | None = None) -> Voxels:
    vox: Voxels = {}
    h = height if height is not None else (frame.height * 2) // 3
    step_rows = max(1, h // depth)
    stair = bs.stairs_toward(variant(pal, "accent", "stairs"), frame.face, "bottom")
    top_slab = bs.slab(variant(pal, "accent", "slab"), "top")

    for v in range(h):
        level = min(depth - 1, v // step_rows)
        cur_depth = depth - level
        next_level = min(depth - 1, (v + 1) // step_rows)
        is_top_of_step = (v == h - 1) or (next_level != level)
        for w in range(2):
            for d in range(1, cur_depth + 1):
                vox[frame.world(u + w, v, d)] = pal.accent
            if is_top_of_step:
                vox[frame.world(u + w, v, cur_depth)] = stair
    for w in range(2):
        vox[frame.world(u + w, h, 1)] = top_slab
    return vox


# ---------------------------------------------------------------------------
# 10. spire
# ---------------------------------------------------------------------------
def spire(x0: int, z0: int, x1: int, z1: int, y_base: int, pal: Palette, height: int) -> Voxels:
    vox: Voxels = {}
    roof_block = pal.roof
    roof_stairs_base = variant(pal, "roof", "stairs")
    cx0, cz0, cx1, cz1 = x0, z0, x1, z1
    span = max(x1 - x0 + 1, z1 - z0 + 1)
    rows_per_step = max(1, round(height / max(1.0, span / 2)))

    y = y_base
    row = 0
    while cx1 >= cx0 and cz1 >= cz0 and (y - y_base) < height:
        for xx in range(cx0, cx1 + 1):
            for zz in range(cz0, cz1 + 1):
                vox[(xx, y, zz)] = roof_block
        for xx in range(cx0, cx1 + 1):
            vox[(xx, y, cz0)] = bs.stairs_toward(roof_stairs_base, "n", "bottom")
            vox[(xx, y, cz1)] = bs.stairs_toward(roof_stairs_base, "s", "bottom")
        for zz in range(cz0, cz1 + 1):
            vox[(cx0, y, zz)] = bs.stairs_toward(roof_stairs_base, "w", "bottom")
            vox[(cx1, y, zz)] = bs.stairs_toward(roof_stairs_base, "e", "bottom")
        row += 1
        y += 1
        if row % rows_per_step == 0:
            cx0 += 1
            cz0 += 1
            cx1 -= 1
            cz1 -= 1

    cx_mid, cz_mid = (cx0 + cx1) // 2, (cz0 + cz1) // 2
    wall_block = bs.wall(variant(pal, "roof", "wall"))
    vox[(cx_mid, y, cz_mid)] = wall_block
    vox[(cx_mid, y + 1, cz_mid)] = wall_block
    vox[(cx_mid, y + 2, cz_mid)] = f"{pal.light}[facing=up]"
    return vox


# ---------------------------------------------------------------------------
# 11. door_opening
# ---------------------------------------------------------------------------
def door_opening(frame: Frame, pal: Palette, u: int, width: int = 2, height: int = 3) -> Voxels:
    vox: Voxels = {}
    door_rows = min(2, height)
    arch_rows = max(0, height - door_rows)
    max_inset = (width - 1) // 2

    opening: set[tuple[int, int]] = {(uu, r) for r in range(door_rows) for uu in range(width)}
    for j in range(arch_rows):
        inset = min(j // 2, max_inset)
        left, right = inset, width - 1 - inset
        row = door_rows + j
        for uu in range(left, right + 1):
            opening.add((uu, row))
    outline = _outline_of(opening)

    for (uu, r) in outline:
        vox[frame.world(u + uu, r, 0)] = pal.accent

    door_base = variant(pal, "trim", "door")
    facing = _facing_word(frame.face)
    # Clear the whole opening through the wall's relief layer (d=+1) AND its thickness
    # (d<0) -- a real archway cuts through any pilaster/plinth relief too -- then put the
    # door leaves back at d=0.
    for uu in range(width):
        for d in range(2, -frame.thickness, -1):
            for r in range(door_rows):
                vox[frame.world(u + uu, r, d)] = AIR
        hinge = "left" if uu < width / 2 else "right"
        if door_rows > 0:
            vox[frame.world(u + uu, 0, 0)] = bs.door(door_base, facing, "lower", hinge=hinge)
        if door_rows > 1:
            vox[frame.world(u + uu, 1, 0)] = bs.door(door_base, facing, "upper", hinge=hinge)

    for (uu, r) in opening:
        if r >= door_rows:
            for d in range(1, -frame.thickness, -1):
                vox[frame.world(u + uu, r, d)] = AIR

    step = bs.stairs_toward(variant(pal, "secondary", "stairs"), frame.face, half="bottom")
    for uu in range(-1, width + 1):
        vox[frame.world(u + uu, -1, 1)] = step
    return vox


# ---------------------------------------------------------------------------
# 13. plinth
# ---------------------------------------------------------------------------
def plinth(
    x0: int,
    z0: int,
    x1: int,
    z1: int,
    y0: int,
    pal: Palette,
    height: int | None = None,
    projection: int = 1,
) -> Voxels:
    """Foundation base around a rectangular footprint: an `accent` course (or two)
    projecting `projection` blocks outward on all four sides, filled solid (a ring band
    plus the fill under the walls), chamfered into the wall above with inverted stairs."""
    vox: Voxels = {}
    xlo, xhi = min(x0, x1), max(x0, x1)
    zlo, zhi = min(z0, z1), max(z0, z1)
    width = xhi - xlo + 1
    depth = zhi - zlo + 1
    if height is None:
        height = 1 if max(width, depth) < 20 else 2

    px0, px1 = xlo - projection, xhi + projection
    pz0, pz1 = zlo - projection, zhi + projection

    for y in range(y0, y0 + height):
        for x in range(px0, px1 + 1):
            for z in range(pz0, pz1 + 1):
                vox[(x, y, z)] = pal.accent

    y_chamfer = y0 + height
    stair_block = variant(pal, "accent", "stairs")
    for x in range(px0, px1 + 1):
        vox[(x, y_chamfer, pz0)] = bs.stairs_toward(stair_block, "n", half="top")
        vox[(x, y_chamfer, pz1)] = bs.stairs_toward(stair_block, "s", half="top")
    for z in range(pz0, pz1 + 1):
        vox[(px0, y_chamfer, z)] = bs.stairs_toward(stair_block, "w", half="top")
        vox[(px1, y_chamfer, z)] = bs.stairs_toward(stair_block, "e", half="top")

    return vox


# ---------------------------------------------------------------------------
# 14. beam
# ---------------------------------------------------------------------------
def beam(x0: int, z0: int, x1: int, z1: int, y: int, pal: Palette, braces: bool = True) -> Voxels:
    """A horizontal log beam along an axis-parallel line, with 2-step inverted-stair
    arch braces at each end (per the sample: beams carry visible load into the walls
    or pillars they land on)."""
    vox: Voxels = {}
    if x0 != x1 and z0 != z1:
        raise ValueError("beam must be axis-parallel (x0 == x1 or z0 == z1)")

    log_block = bs.log(variant(pal, "trim", "log"), "x" if z0 == z1 else "z")
    stair_block = variant(pal, "trim", "stairs")

    if z0 == z1:
        lo, hi = min(x0, x1), max(x0, x1)
        for x in range(lo, hi + 1):
            vox[(x, y, z0)] = log_block
        if braces:
            vox[(lo, y - 1, z0)] = bs.stairs_toward(stair_block, "e", half="top")
            vox[(lo + 1, y - 2, z0)] = bs.stairs_toward(stair_block, "e", half="top")
            vox[(hi, y - 1, z0)] = bs.stairs_toward(stair_block, "w", half="top")
            vox[(hi - 1, y - 2, z0)] = bs.stairs_toward(stair_block, "w", half="top")
    else:
        lo, hi = min(z0, z1), max(z0, z1)
        for z in range(lo, hi + 1):
            vox[(x0, y, z)] = log_block
        if braces:
            vox[(x0, y - 1, lo)] = bs.stairs_toward(stair_block, "s", half="top")
            vox[(x0, y - 2, lo + 1)] = bs.stairs_toward(stair_block, "s", half="top")
            vox[(x0, y - 1, hi)] = bs.stairs_toward(stair_block, "n", half="top")
            vox[(x0, y - 2, hi - 1)] = bs.stairs_toward(stair_block, "n", half="top")

    return vox
