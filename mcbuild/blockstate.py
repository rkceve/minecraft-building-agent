"""Block-state string builders and the two geometry post-passes.

A block id string looks like `"oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"`
(no `minecraft:` prefix; property order inside `[...]` is always the sorted-key order).

Stairs `facing` semantics (vanilla, verified against BlockStateProperties / StairsBlock):
`facing` is the direction the stair *rises toward* -- the tall (back, full-height) part of
the stair sits on the `facing` side of the block, and the low single-height step is on the
opposite side. Standing at the low step looking at the tall part, you look toward `facing`.

    facing=north:              facing=south:
        N (tall, full height)      N (low step)
        |#|                        |_|
        |_|  <- low step (south)   |#|  <- tall (north... wait, see picture below)

Picture for facing=north (side view, looking along +x, N is -z / up in this ASCII, S is +z / down):
    z=north (-z) ............ z=south (+z)
    #  <- full height block (the back of the stair, at the `facing` = north side... )
    _  <- the low step is on the +z (south) side

So the HIGH side is on the `facing` side and the LOW step is on the opposite side.
`stairs_toward(block, face, half)` builds a stair whose LOW step points toward `face`
(the outward direction, away from a building) -- used for eaves/roofs/sills where the
low, walkable-looking edge should face outward. Since low points to `face`, the high
side (and therefore vanilla `facing`) points the opposite way:

    stairs_toward(b, "n", ...) -> facing="s"   (low step points north, tall side south)
    stairs_toward(b, "s", ...) -> facing="n"
    stairs_toward(b, "e", ...) -> facing="w"
    stairs_toward(b, "w", ...) -> facing="e"
"""
from __future__ import annotations

from mcbuild.litematic import Voxels

__all__ = [
    "stairs",
    "slab",
    "log",
    "wall",
    "fence",
    "trapdoor",
    "door",
    "pane",
    "rotate_state",
    "stairs_toward",
    "connect_fences_and_walls",
    "fix_stair_corners",
]

_OPPOSITE_FACE = {"n": "s", "s": "n", "e": "w", "w": "e"}
_FACE_TO_FACING = {"n": "north", "s": "south", "e": "east", "w": "west"}


def _parse(block: str) -> tuple[str, dict[str, str]]:
    if "[" not in block:
        return block, {}
    base, rest = block.split("[", 1)
    rest = rest.rstrip("]")
    props: dict[str, str] = {}
    if rest:
        for pair in rest.split(","):
            k, v = pair.split("=", 1)
            props[k] = v
    return base, props


def _serialize(base: str, props: dict[str, str]) -> str:
    if not props:
        return base
    inner = ",".join(f"{k}={v}" for k, v in sorted(props.items()))
    return f"{base}[{inner}]"


def _bool(v: bool) -> str:
    return "true" if v else "false"


def stairs(block: str, facing: str, half: str = "bottom", shape: str = "straight") -> str:
    return _serialize(block, {"facing": facing, "half": half, "shape": shape, "waterlogged": "false"})


def stairs_toward(block: str, outward_face: str, half: str = "bottom") -> str:
    """Stair whose LOW step points toward `outward_face`. See module docstring truth table."""
    facing = _FACE_TO_FACING[_OPPOSITE_FACE[outward_face]]
    return stairs(block, facing, half=half)


def slab(block: str, kind: str = "bottom") -> str:
    return _serialize(block, {"type": kind, "waterlogged": "false"})


def log(block: str, axis: str) -> str:
    return _serialize(block, {"axis": axis})


def wall(block: str, up: bool = True, **sides: str) -> str:
    props: dict[str, str] = {"north": "none", "east": "none", "south": "none", "west": "none"}
    for k, v in sides.items():
        if k not in ("north", "east", "south", "west"):
            raise ValueError(f"unknown wall side {k!r}")
        props[k] = v
    props["up"] = _bool(up)
    props["waterlogged"] = "false"
    return _serialize(block, props)


def fence(block: str, **sides: bool) -> str:
    props: dict[str, bool] = {"north": False, "east": False, "south": False, "west": False}
    for k, v in sides.items():
        if k not in props:
            raise ValueError(f"unknown fence side {k!r}")
        props[k] = v
    out: dict[str, str] = {k: _bool(v) for k, v in props.items()}
    out["waterlogged"] = "false"
    return _serialize(block, out)


def trapdoor(block: str, facing: str, half: str = "bottom", open: bool = False) -> str:
    return _serialize(block, {"facing": facing, "half": half, "open": _bool(open), "waterlogged": "false"})


def door(block: str, facing: str, half: str, hinge: str = "left", open: bool = False) -> str:
    return _serialize(block, {"facing": facing, "half": half, "hinge": hinge, "open": _bool(open)})


def pane(block: str, **sides: bool) -> str:
    props: dict[str, bool] = {"north": False, "east": False, "south": False, "west": False}
    for k, v in sides.items():
        if k not in props:
            raise ValueError(f"unknown pane side {k!r}")
        props[k] = v
    out: dict[str, str] = {k: _bool(v) for k, v in props.items()}
    out["waterlogged"] = "false"
    return _serialize(block, out)


_FACING_CW = ["north", "east", "south", "west"]
_SIDE_CW = ["north", "east", "south", "west"]


def rotate_state(block: str, quarter_turns: int) -> str:
    """Rotate `facing`, `axis` and the four side properties by `quarter_turns` steps of
    90 degrees clockwise (viewed from above, around the y axis). `shape` (outer_left/
    outer_right/inner_left/inner_right/straight) and `hinge` are left unchanged, matching
    vanilla structure-block rotation of stairs and doors.
    """
    base, props = _parse(block)
    n = quarter_turns % 4
    if n == 0:
        return block
    new_props = dict(props)

    if "facing" in props and props["facing"] in _FACING_CW:
        idx = _FACING_CW.index(props["facing"])
        new_props["facing"] = _FACING_CW[(idx + n) % 4]

    if "axis" in props and props["axis"] in ("x", "z") and n % 2 == 1:
        new_props["axis"] = "z" if props["axis"] == "x" else "x"

    if any(k in props for k in _SIDE_CW):
        old_vals = {k: props[k] for k in _SIDE_CW if k in props}
        for _ in range(n):
            rotated: dict[str, str] = {}
            for i, k in enumerate(_SIDE_CW):
                src = _SIDE_CW[(i - 1) % 4]
                if src in old_vals:
                    rotated[k] = old_vals[src]
            old_vals = rotated
        for k, v in old_vals.items():
            new_props[k] = v

    return _serialize(base, new_props)


# ---------------------------------------------------------------------------
# Post-passes
# ---------------------------------------------------------------------------

_DELTA = {"n": (0, 0, -1), "s": (0, 0, 1), "e": (1, 0, 0), "w": (-1, 0, 0)}
_SIDE_TO_DELTA = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def _is_solid(block: str) -> bool:
    """A conservative "is this a full/solid block for connection purposes" check: not a
    stair/slab/fence/wall/pane/trapdoor/door and not a partial or transparent block.
    """
    base = block.split("[", 1)[0]
    if base in ("air",):
        return False
    if any(base.endswith(sfx) for sfx in ("_stairs", "_slab", "_fence", "_fence_gate", "_wall", "_pane", "_trapdoor", "_door")):
        return False
    return True


def _is_fence_wall_pane(block: str) -> bool:
    base = block.split("[", 1)[0]
    return any(base.endswith(sfx) for sfx in ("_fence", "_wall", "_pane"))


def connect_fences_and_walls(vox: Voxels) -> None:
    """In-place post-pass: sets north/east/south/west (and, for walls, up) on every
    fence/pane/wall block based on its neighbours, per DSL.md item 12.
    """
    for (x, y, z), block in list(vox.items()):
        base = block.split("[", 1)[0]
        is_wall = base.endswith("_wall")
        is_fence = base.endswith("_fence") and not base.endswith("_fence_gate")
        is_pane = base.endswith("_pane")
        if not (is_wall or is_fence or is_pane):
            continue

        sides: dict[str, str | bool] = {}
        wall_neighbour_count = 0
        for side, (dx, dz) in _SIDE_TO_DELTA.items():
            neighbour = vox.get((x + dx, y, z + dz))
            connects = neighbour is not None and (_is_fence_wall_pane(neighbour) or _is_solid(neighbour))
            if is_wall:
                sides[side] = "low" if connects else "none"
                if connects:
                    wall_neighbour_count += 1
            else:
                sides[side] = bool(connects)

        if is_wall:
            above = vox.get((x, y + 1, z))
            has_block_above = above is not None
            # up=true when there is a block above, or when there are no wall/fence/pane
            # connections on opposite sides holding the wall's cap flat.
            opposite_pairs_connected = (sides["north"] == "low" and sides["south"] == "low") or (
                sides["east"] == "low" and sides["west"] == "low"
            )
            up = has_block_above or not opposite_pairs_connected or wall_neighbour_count == 0
            vox[(x, y, z)] = wall(base, up=up, **sides)  # type: ignore[arg-type]
        elif is_fence:
            vox[(x, y, z)] = fence(base, **sides)  # type: ignore[arg-type]
        else:
            vox[(x, y, z)] = pane(base, **sides)  # type: ignore[arg-type]


def _perp_and_relation(a_facing: str, b_facing: str) -> str | None:
    """Given two stair `facing` values, return "ccw" if b is the counter-clockwise
    rotation of a, "cw" if clockwise, or None if they are parallel (not perpendicular).
    """
    if a_facing == b_facing or _OPPOSITE_FACING.get(a_facing) == b_facing:
        return None
    idx_a = _FACING_CW.index(a_facing)
    idx_b = _FACING_CW.index(b_facing)
    if (idx_a + 1) % 4 == idx_b:
        return "cw"
    if (idx_a - 1) % 4 == idx_b:
        return "ccw"
    return None


_OPPOSITE_FACING = {"north": "south", "south": "north", "east": "west", "west": "east"}
_FACING_TO_DELTA = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0)}


def fix_stair_corners(vox: Voxels) -> None:
    """In-place post-pass implementing vanilla StairsBlock.getStairsShape: for every
    stair block, look at the neighbour in the `facing` direction and the neighbour
    opposite it to decide outer_left/outer_right/inner_left/inner_right/straight.

    Vanilla algorithm (simplified to the same-half case used by this DSL):
      - Let `front` = the stair in front of us (position + facing delta).
        If `front` is a stair with the same half and a facing perpendicular to ours,
        this is an OUTER corner. It is outer_right if front.facing is the clockwise
        rotation of our facing, else outer_left. (Vanilla determines left/right by
        which side the corner falls on; for the CW/CCW pairing used here this matches
        the vanilla table: our facing -> front is our CW neighbour => outer_right,
        front is our CCW neighbour => outer_left.)
      - Otherwise let `back` = the stair behind us (position - facing delta).
        If `back` is a stair with the same half and a facing perpendicular to ours,
        this is an INNER corner: inner_right if back.facing is the clockwise rotation
        of our facing, else inner_left.
      - Otherwise shape=straight.
    """
    for pos, block in list(vox.items()):
        base, props = _parse(block)
        if not base.endswith("_stairs"):
            continue
        facing = props.get("facing")
        half = props.get("half", "bottom")
        if facing not in _FACING_TO_DELTA:
            continue
        x, y, z = pos
        dx, dy, dz = _FACING_TO_DELTA[facing]
        front = vox.get((x + dx, y + dy, z + dz))
        back = vox.get((x - dx, y - dy, z - dz))

        shape = "straight"
        if front is not None:
            fbase, fprops = _parse(front)
            if fbase.endswith("_stairs") and fprops.get("half", "bottom") == half:
                rel = _perp_and_relation(facing, fprops.get("facing", ""))
                if rel == "cw":
                    shape = "outer_right"
                elif rel == "ccw":
                    shape = "outer_left"
        if shape == "straight" and back is not None:
            bbase, bprops = _parse(back)
            if bbase.endswith("_stairs") and bprops.get("half", "bottom") == half:
                rel = _perp_and_relation(facing, bprops.get("facing", ""))
                if rel == "cw":
                    shape = "inner_right"
                elif rel == "ccw":
                    shape = "inner_left"

        props["shape"] = shape
        vox[pos] = _serialize(base, props)
