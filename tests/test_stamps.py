from __future__ import annotations

from mcbuild import stamps as st
from mcbuild.ascii import elevation
from mcbuild.litematic import load_voxels
from mcbuild.techniques import AIR, Frame


def test_extract_and_place_round_trips_on_north_frame() -> None:
    vox = load_voxels(st.CATHEDRAL_PATH)
    x0, y0, z0, x1, y1, z1 = st.WINDOW_BAY_BOX
    stamp = st.extract_stamp(vox, x0, y0, z0, x1, y1, z1, face="n")
    frame = Frame("n", x1, y0, z1 - 1, x1 - x0 + 1, y1 - y0 + 1, thickness=1)
    placed = stamp.place(frame)
    original = {p: b for p, b in vox.items() if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and z0 <= p[2] <= z1}
    assert placed == original


def test_place_on_east_frame_and_back_matches_original_multiset() -> None:
    vox = load_voxels(st.CATHEDRAL_PATH)
    x0, y0, z0, x1, y1, z1 = st.WINDOW_BAY_BOX
    stamp = st.extract_stamp(vox, x0, y0, z0, x1, y1, z1, face="n")

    east_frame = Frame("e", 0, 0, 0, x1 - x0 + 1, y1 - y0 + 1, thickness=1)
    placed_east = stamp.place(east_frame)
    assert len(placed_east) == len(stamp.cells)

    # rotate back: reinterpret the east placement as a stamp captured on face "e"
    # (turns 0 relative to itself) and place it back on a north frame -- must
    # reproduce the exact same base-block multiset as the original stamp.
    def base(block: str) -> str:
        return block.split("[")[0]

    original_bases = sorted(base(b) for b in stamp.cells.values())
    east_bases = sorted(base(b) for b in placed_east.values())
    assert original_bases == east_bases


def test_cathedral_window_5x10_has_opening_fence_and_stairs() -> None:
    cells = st.cathedral_window_cells(width=5, height=10, thickness=1)
    vs = sorted({v for (_u, v, _d) in cells})
    assert len(vs) == 10
    has_air = any(b == AIR for b in cells.values())
    assert has_air, "expected at least one air opening cell"
    fence_center = [
        b for (u, _v, _d), b in cells.items() if u == st.WINDOW_CENTER_U - ((11 - 5) // 2) and "fence" in b
    ]
    assert fence_center, "expected a fence (mullion) in the center column"
    stair_blocks = [b for b in cells.values() if "_stairs" in b]
    assert stair_blocks, "expected stair blocks somewhere in the window"


def test_cathedral_window_height_matches_request() -> None:
    for width, height in ((5, 10), (7, 22), (3, 8), (9, 14)):
        cells = st.cathedral_window_cells(width=width, height=height, thickness=1)
        vs = {v for (_u, v, _d) in cells}
        assert max(vs) - min(vs) + 1 <= height
        us = {u for (u, _v, _d) in cells}
        assert all(0 <= u < width for u in us)


def test_cathedral_window_all_four_faces_same_multiset() -> None:
    def base(block: str) -> str:
        return block.split("[")[0]

    cells = st.cathedral_window_cells(width=5, height=10, thickness=1)
    non_air = {k: b for k, b in cells.items() if b != AIR}
    multisets = []
    for face in ("n", "s", "e", "w"):
        frame = Frame(face, 0, 0, 0, 5, 10, thickness=1)
        placed = st.window_frame_cathedral(frame, 0, 0, 5, 10, thickness=1)
        placed_non_air = {p: b for p, b in placed.items() if b != AIR}
        multisets.append(sorted(base(b) for b in placed_non_air.values()))
    assert len(non_air) > 0
    for m in multisets[1:]:
        assert m == multisets[0]


def test_preview_ascii_smoke() -> None:
    cells = st.cathedral_window_cells(width=5, height=10, thickness=1)
    frame = Frame("n", 0, 0, 0, 5, 10, thickness=1)
    vox = {}
    for (u, v, d), b in cells.items():
        if b == AIR:
            continue
        vox[frame.world(u, v, d)] = b
    art = elevation(vox, "n")
    assert art
