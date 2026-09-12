from __future__ import annotations

import importlib.util
from pathlib import Path

from mcbuild import techniques as tq
from mcbuild.dsl import Build
from mcbuild.palette import Palette

FIXTURES = Path(__file__).parent / "fixtures"


def _load_chapel() -> Build:
    spec = importlib.util.spec_from_file_location("chapel", FIXTURES / "chapel.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build()


def test_chapel_builds_and_checks_clean() -> None:
    b = _load_chapel()
    vox = b.voxels()
    assert len(vox) > 0
    warnings = b.check()
    assert warnings == [], warnings


def _roof_positions(vox, ridge: str, x0, z0, x1, z1, overhang, y_top):
    """Return, for every column of the roof footprint, whether a downward ray from
    y_top hits a block, and (for run-contiguity) the set of occupied cells per row."""
    hits = {}
    for x in range(x0 - overhang, x1 + overhang + 1):
        for z in range(z0 - overhang, z1 + overhang + 1):
            hit = any((x, y, z) in vox for y in range(y_top, -1, -1))
            hits[(x, z)] = hit
    return hits


def test_roof_is_watertight_and_stairs_contiguous() -> None:
    b = _load_chapel()
    vox = b.voxels()

    x0, z0, x1, z1 = 0, 1, 14, 24  # world coords (origin y offset doesn't matter here)
    overhang = 1
    y_top = 60

    hits = _roof_positions(vox, "z", x0, z0, x1, z1, overhang, y_top)
    missing = [pos for pos, hit in hits.items() if not hit]
    assert missing == [], f"roof has holes at {missing}"

    # run-length contiguity check: each roof stair line runs the full length of the roof
    # (along the ridge-parallel axis, here z since the chapel's ridge runs along z) at a
    # fixed (x, y) -- it must have no internal gaps.
    stair_cells = [pos for pos, block in vox.items() if "_stairs" in block.split("[")[0] and pos[1] > 13]
    by_xy: dict[tuple[int, int], set[int]] = {}
    for x, y, z in stair_cells:
        by_xy.setdefault((x, y), set()).add(z)
    for (x, y), zs in by_xy.items():
        lo, hi = min(zs), max(zs)
        gap = set(range(lo, hi + 1)) - zs
        assert not gap, f"roof stair line at x={x},y={y} not contiguous, missing z={sorted(gap)}"


def test_windows_have_air_and_glass() -> None:
    b = _load_chapel()
    vox = b.voxels()
    prov = b.provenance()

    window_ids = [eid for eid, m in b.elements().items() if m["kind"] == "window"]
    assert window_ids

    has_glass = {eid: False for eid in window_ids}
    for pos, eid in prov.items():
        if eid in has_glass:
            block = vox[pos]
            if "glass" in block or "pane" in block:
                has_glass[eid] = True

    for eid, found in has_glass.items():
        assert found, f"window {eid} has no glass panes in the final voxel set"


def test_provenance_covers_all_voxels() -> None:
    b = _load_chapel()
    vox = b.voxels()
    prov = b.provenance()
    assert set(vox.keys()) == set(prov.keys())
    assert len(prov) == len(vox)


def test_corner_pillars_overwrite_wall_corners() -> None:
    b = _load_chapel()
    vox = b.voxels()

    ox, oy, oz = b.origin
    y0 = 1
    x0, z0, x1, z1 = 0, 0, 14, 24
    corner_y = oy + y0 + 1  # a layer well inside the pillar column, above the plinth

    for cx, cz in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        pos = (cx + ox, corner_y, cz + oz)
        block = vox[pos]
        base = block.split("[")[0]
        assert base.endswith("_wall"), f"corner {pos} is {block!r}, expected the pillar ring wall block"


def test_plinth_ring_present_and_pillars_overwrite_it_at_corners() -> None:
    b = _load_chapel()
    vox = b.voxels()

    ox, oy, oz = b.origin
    y0 = 1
    x0, z0, x1, z1 = 0, 0, 14, 24

    # Plinth ring: one block outside the footprint (projection=1) at y0 must be `accent`
    # (deepslate_bricks) except where a corner pillar overwrites it.
    pos = (x0 - 1 + ox, y0 + oy, (z0 + z1) // 2 + oz)  # west side, mid-length, outside footprint
    block = vox[pos]
    assert block.split("[")[0] == b.palette.accent

    # At the corners, the pillar (drawn after the plinth) overwrites the plinth's ring
    # block at y0+1 with its own ring wall block -- the pillar stands "through" the base.
    corner_y = oy + y0 + 1
    for cx, cz in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        cpos = (cx + ox, corner_y, cz + oz)
        cblock = vox[cpos]
        assert cblock.split("[")[0].endswith("_wall"), f"corner {cpos} is {cblock!r}, expected pillar ring"


def test_beam_has_braces_at_both_ends() -> None:
    pal = Palette()
    vox = tq.beam(0, 0, 10, 0, 10, pal, braces=True)

    log_positions = [pos for pos, block in vox.items() if "_log" in block]
    assert len(log_positions) == 11

    stair_positions = {pos: block for pos, block in vox.items() if "_stairs" in block}
    assert (0, 9, 0) in stair_positions
    assert (1, 8, 0) in stair_positions
    assert (10, 9, 0) in stair_positions
    assert (9, 8, 0) in stair_positions

    # low step of each brace stair points toward the beam's centre
    from mcbuild import blockstate as bs

    end_block = stair_positions[(0, 9, 0)].split("[")[0]
    other_end_block = stair_positions[(10, 9, 0)].split("[")[0]
    assert stair_positions[(0, 9, 0)] == bs.stairs_toward(end_block, "e", half="top")
    assert stair_positions[(10, 9, 0)] == bs.stairs_toward(other_end_block, "w", half="top")


def test_beam_without_braces_has_no_stairs() -> None:
    pal = Palette()
    vox = tq.beam(0, 0, 10, 0, 10, pal, braces=False)
    assert not any("_stairs" in block for block in vox.values())


def test_ridge_ornament_present_for_odd_span_absent_for_even() -> None:
    pal = Palette()

    # odd perpendicular span (z: 0..6, 7 wide) -> single-row ridge, decorated
    odd_vox = tq.gable_roof(0, 0, 20, 6, 0, pal, ridge="x", overhang=0)
    odd_walls = {pos: b for pos, b in odd_vox.items() if b.split("[")[0].endswith("_wall")}
    assert odd_walls, "expected ridge ornament wall posts/finials for an odd span"

    # finials at both gable ends of the ridge (x = 0 and x = 20), 2 tall, accent family
    finial_base = odd_walls[(0, 4, 3)].split("[")[0]
    assert finial_base == odd_walls[(0, 5, 3)].split("[")[0] == finial_base
    assert (0, 6, 3) in odd_vox and odd_vox[(0, 6, 3)].startswith(pal.light)
    assert (20, 6, 3) in odd_vox and odd_vox[(20, 6, 3)].startswith(pal.light)

    # even perpendicular span (z: 0..5, 6 wide) -> two stair lines meeting, no ridge wall blocks
    even_vox = tq.gable_roof(0, 0, 20, 5, 0, pal, ridge="x", overhang=0)
    even_walls = {pos: b for pos, b in even_vox.items() if b.split("[")[0].endswith("_wall")}
    assert not even_walls, "even span must not get ridge ornament"


def test_check_warns_on_even_width_room() -> None:
    b = Build(origin=(0, 1, 0), palette=Palette())
    b.room(0, 0, 15, 10, 1, 6, id="room_1")  # width = 16, even
    warnings = b.check()
    assert any("room_1 is 16 wide" in w for w in warnings), warnings


def test_check_no_width_warning_for_odd_room() -> None:
    b = Build(origin=(0, 1, 0), palette=Palette())
    b.room(0, 0, 14, 10, 1, 6, id="room_1")  # width = 15, odd
    warnings = b.check()
    assert not any("widths should be odd" in w for w in warnings), warnings
