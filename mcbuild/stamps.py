"""Literal voxel "stamps" cut from refs/cathedral.litematic, re-expressed in a
face-local (u, v, d) frame so they can be replayed onto any wall Frame via
Frame.world + blockstate.rotate_state, instead of a hand-written parametric
approximation.

Catalog is cached to catalog/cathedral_stamps.json (rebuild with
`python -m mcbuild.stamps --rebuild`) so the .litematic file is not parsed at
import time in normal test/preview runs.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .blockstate import rotate_state
from .litematic import Voxels, load_voxels
from .techniques import AIR, Frame

__all__ = [
    "Stamp",
    "extract_stamp",
    "get_catalog",
    "build_catalog",
    "cathedral_window_cells",
    "window_frame_cathedral",
]

_FACE_TURNS = {"s": 0, "w": 1, "n": 2, "e": 3}
_ROOT = Path(__file__).resolve().parent.parent
CATHEDRAL_PATH = _ROOT / "refs" / "cathedral.litematic"
CATALOG_PATH = _ROOT / "catalog" / "cathedral_stamps.json"

# The reference window bay: x=50..60 (width 11, u=0 at x=60), y=0..25, z=19..22
# (wall plane at z=21 -> d=0; z=20 -> d=1; z=19 -> d=2; z=22 -> d=-1, interior).
WINDOW_BAY_BOX = (50, 0, 19, 60, 25, 22)
WINDOW_BAY_WIDTH = 11
WINDOW_SILL_V = range(0, 4)
WINDOW_BODY_UNIT_V = (4, 5, 6)
WINDOW_ARCH_V = range(10, 26)
WINDOW_CENTER_U = 5


def _turns_between(src_face: str, dst_face: str) -> int:
    return (_FACE_TURNS[dst_face] - _FACE_TURNS[src_face]) % 4


@dataclass(frozen=True)
class Stamp:
    """A captured voxel pattern in (u, v, d) coordinates, expressed as if seen
    from face "n" (see extract_stamp). `place` replays it onto any Frame."""

    cells: dict[tuple[int, int, int], str]
    width: int
    height: int
    d_min: int
    d_max: int
    face: str = "n"

    def place(self, frame: Frame, u0: int = 0, v0: int = 0) -> Voxels:
        turns = _turns_between(self.face, frame.face)
        out: Voxels = {}
        for (u, v, d), block in self.cells.items():
            pos = frame.world(u0 + u, v0 + v, d)
            out[pos] = block if block == AIR else rotate_state(block, turns)
        return out

    def rows(self) -> dict[int, dict[tuple[int, int], str]]:
        """Group cells by v -> {(u, d): block}."""
        out: dict[int, dict[tuple[int, int], str]] = {}
        for (u, v, d), block in self.cells.items():
            out.setdefault(v, {})[(u, d)] = block
        return out


def extract_stamp(
    vox: Voxels, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int, face: str = "n"
) -> Stamp:
    """Cut a box out of `vox` into a local (u, v, d) frame, expressed for face "n"."""
    xlo, xhi = min(x0, x1), max(x0, x1)
    ylo, yhi = min(y0, y1), max(y0, y1)
    zlo, zhi = min(z0, z1), max(z0, z1)

    if face in ("n", "s"):
        depth_lo, depth_hi = zlo, zhi
        along_lo, along_hi = xlo, xhi
    else:
        depth_lo, depth_hi = xlo, xhi
        along_lo, along_hi = zlo, zhi

    if face == "n":
        wall_plane, u_ref = depth_hi - 1, along_hi
    elif face == "s":
        wall_plane, u_ref = depth_lo + 1, along_lo
    elif face == "e":
        wall_plane, u_ref = depth_lo + 1, along_lo
    else:  # w
        wall_plane, u_ref = depth_hi - 1, along_hi

    cells: dict[tuple[int, int, int], str] = {}
    for (x, y, z), block in vox.items():
        if not (xlo <= x <= xhi and ylo <= y <= yhi and zlo <= z <= zhi):
            continue
        v = y - ylo
        if face == "n":
            u, d = u_ref - x, wall_plane - z
        elif face == "s":
            u, d = x - u_ref, z - wall_plane
        elif face == "e":
            u, d = u_ref - z, x - wall_plane
        else:
            u, d = z - u_ref, wall_plane - x
        cells[(u, v, d)] = block

    if face != "n":
        turns = _turns_between(face, "n")
        cells = {k: rotate_state(b, turns) for k, b in cells.items()}

    width = along_hi - along_lo + 1
    height = yhi - ylo + 1
    ds = [c[2] for c in cells] or [0]
    return Stamp(cells=cells, width=width, height=height, d_min=min(ds), d_max=max(ds), face="n")


# ---------------------------------------------------------------------------
# catalog cache
# ---------------------------------------------------------------------------
def _serialize_stamp(s: Stamp) -> dict:
    return {
        "width": s.width,
        "height": s.height,
        "d_min": s.d_min,
        "d_max": s.d_max,
        "face": s.face,
        "cells": [[u, v, d, b] for (u, v, d), b in s.cells.items()],
    }


def _deserialize_stamp(data: dict) -> Stamp:
    cells = {(u, v, d): b for u, v, d, b in data["cells"]}
    return Stamp(
        cells=cells,
        width=data["width"],
        height=data["height"],
        d_min=data["d_min"],
        d_max=data["d_max"],
        face=data.get("face", "n"),
    )


def build_catalog(cathedral_path: Path = CATHEDRAL_PATH) -> dict[str, Stamp]:
    vox = load_voxels(cathedral_path)
    return {"window_bay": extract_stamp(vox, *WINDOW_BAY_BOX)}


def _write_catalog(stamps: dict[str, Stamp], path: Path = CATALOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: _serialize_stamp(v) for k, v in stamps.items()}), encoding="utf-8")


def _read_catalog(path: Path = CATALOG_PATH) -> dict[str, Stamp] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: _deserialize_stamp(v) for k, v in data.items()}


_CATALOG: dict[str, Stamp] | None = None


def get_catalog() -> dict[str, Stamp]:
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG
    cached = _read_catalog()
    if cached is None:
        cached = build_catalog()
        _write_catalog(cached)
    _CATALOG = cached
    return _CATALOG


# ---------------------------------------------------------------------------
# cathedral window: structured crop/tile of the window_bay stamp
# ---------------------------------------------------------------------------
def _crop_row(row: dict[tuple[int, int], str], keep_us: range, u_offset: int) -> dict[tuple[int, int], str]:
    return {(u - u_offset, d): b for (u, d), b in row.items() if u in keep_us}


def cathedral_window_cells(width: int, height: int, thickness: int = 1) -> dict[tuple[int, int, int], str]:
    """Local (u, v, d) -> block dict (u in 0..width-1, v in 0..height-1) for a
    cathedral-style window, cropped/tiled from the real window_bay stamp.
    `AIR` markers cut the opening through the wall's thickness.

    Raises ValueError for sizes outside the supported cathedral range (odd
    width 3..11, height >= 8) -- callers should fall back to the parametric
    "pointed" style for anything else.
    """
    if width < 3 or width > 11 or width % 2 == 0 or height < 8:
        raise ValueError("cathedral window requires odd width 3..11 and height >= 8")

    bay = get_catalog()["window_bay"]
    rows = bay.rows()
    crop = (WINDOW_BAY_WIDTH - width) // 2
    keep_us = range(crop, WINDOW_BAY_WIDTH - crop)

    def cropped(v: int) -> dict[tuple[int, int], str]:
        return _crop_row(rows.get(v, {}), keep_us, crop)

    sill = [cropped(v) for v in WINDOW_SILL_V]
    body_unit = [cropped(v) for v in WINDOW_BODY_UNIT_V]
    arch_full = [row for v in WINDOW_ARCH_V if (row := cropped(v))]

    budget = max(0, height - len(sill))
    if len(arch_full) <= budget:
        arch_used = arch_full
        body_count = budget - len(arch_full)
        body_rows = [body_unit[i % len(body_unit)] for i in range(body_count)]
    else:
        # not enough room for the full arch: keep a minimum one body period
        # (guarantees a real glazing gap + mullion survive at any size) and
        # give the arch the rest, nearest the springing line (most structural).
        body_count = min(len(body_unit), budget)
        body_rows = [body_unit[i % len(body_unit)] for i in range(body_count)]
        arch_used = arch_full[: budget - body_count]

    assembled = sill + body_rows + arch_used
    while len(assembled) < height:
        assembled.append({})
    assembled = assembled[:height]

    out: dict[tuple[int, int, int], str] = {}
    for v, row in enumerate(assembled):
        occupied_us = {u for (u, _d) in row}
        for (u, d), block in row.items():
            out[(u, v, d)] = block
        for u in range(width):
            if u not in occupied_us:
                for d in range(1, -(thickness - 1) - 1, -1):
                    out[(u, v, d)] = AIR
    return out


def window_frame_cathedral(frame: Frame, u: int, v: int, width: int, height: int, thickness: int = 1) -> Voxels:
    cells = cathedral_window_cells(width, height, thickness=thickness)
    turns = _turns_between("n", frame.face)
    out: Voxels = {}
    for (uu, vv, d), block in cells.items():
        pos = frame.world(u + uu, v + vv, d)
        out[pos] = block if block == AIR else rotate_state(block, turns)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild the cathedral stamp catalog")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args(argv)
    if args.rebuild:
        stamps = build_catalog()
        _write_catalog(stamps)
        print(f"wrote {CATALOG_PATH} ({sum(len(s.cells) for s in stamps.values())} cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
