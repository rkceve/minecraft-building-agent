"""Voxel dicts -> Minecraft console commands (no leading slash).

Commands are ordered ascending y, then z, then x so structures rise from the
ground while the build is streamed to the server.
"""
from __future__ import annotations

import json
from collections.abc import Iterator

from .litematic import Voxels

Box = tuple[int, int, int, int, int, int]

MAX_FILL = 32768
_TILE = 32
_STORAGE_Y = 200
_STORAGE_Z = 100000
_MAX_FORCELOAD_CHUNKS = 16


def bounds(vox: Voxels) -> Box:
    """Inclusive bounding box (x0, y0, z0, x1, y1, z1) of a voxel dict."""
    xs = [p[0] for p in vox]
    ys = [p[1] for p in vox]
    zs = [p[2] for p in vox]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def to_commands(vox: Voxels, origin: tuple[int, int, int] = (0, 0, 0)) -> list[str]:
    """Emit setblock/fill commands, compressing identical runs along +x.

    `origin` is added to every coordinate before emitting.
    """
    ox, oy, oz = origin
    rows: dict[tuple[int, int], list[int]] = {}
    for x, y, z in vox:
        rows.setdefault((y, z), []).append(x)
    out: list[str] = []
    for y, z in sorted(rows):
        xs = sorted(rows[(y, z)])
        start = prev = xs[0]
        block = vox[(start, y, z)]
        for x in xs[1:] + [None]:  # type: ignore[list-item]
            same = x == prev + 1 and x is not None and vox[(x, y, z)] == block
            if not same:
                out.append(_run(start + ox, prev + ox, y + oy, z + oz, block))
                if x is None:
                    break
                start, block = x, vox[(x, y, z)]
            prev = x
    return out


def _run(x0: int, x1: int, y: int, z: int, block: str) -> str:
    count = x1 - x0 + 1
    assert count <= MAX_FILL, f"fill of {count} blocks exceeds {MAX_FILL}"
    if count == 1:
        return f"setblock {x0} {y} {z} {block}"
    return f"fill {x0} {y} {z} {x1} {y} {z} {block}"


def _norm(box: Box) -> Box:
    x0, y0, z0, x1, y1, z1 = box
    return (min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1))


def _tiles(box: Box) -> Iterator[Box]:
    """Split a box into sub-boxes of at most 32 x 32 x 32 blocks."""
    x0, y0, z0, x1, y1, z1 = _norm(box)
    for y in range(y0, y1 + 1, _TILE):
        for z in range(z0, z1 + 1, _TILE):
            for x in range(x0, x1 + 1, _TILE):
                yield (x, y, z, min(x + _TILE - 1, x1), min(y + _TILE - 1, y1), min(z + _TILE - 1, z1))


def _storage_origin(slot: int) -> tuple[int, int, int]:
    return (100000 + slot * 256, _STORAGE_Y, _STORAGE_Z)


def storage_box(box: Box, slot: int) -> Box:
    """The region a backup of `box` occupies in storage slot `slot`."""
    x0, y0, z0, x1, y1, z1 = _norm(box)
    sx, sy, sz = _storage_origin(slot)
    return (sx, sy, sz, sx + (x1 - x0), sy + (y1 - y0), sz + (z1 - z0))


def _shift(tile: Box, box: Box, slot: int) -> tuple[int, int, int]:
    x0, y0, z0 = _norm(box)[:3]
    sx, sy, sz = _storage_origin(slot)
    return (tile[0] - x0 + sx, tile[1] - y0 + sy, tile[2] - z0 + sz)


def backup_commands(box: Box, slot: int) -> list[str]:
    """Clone the site box into the storage area for `slot`, tiled to <= 32768 blocks."""
    out = []
    for t in _tiles(box):
        dx, dy, dz = _shift(t, box, slot)
        out.append(f"clone {t[0]} {t[1]} {t[2]} {t[3]} {t[4]} {t[5]} {dx} {dy} {dz} replace force")
    return out


def restore_commands(box: Box, slot: int) -> list[str]:
    """Clone the storage copy for `slot` back onto the site box."""
    out = []
    for t in _tiles(box):
        dx, dy, dz = _shift(t, box, slot)
        ex, ey, ez = dx + (t[3] - t[0]), dy + (t[4] - t[1]), dz + (t[5] - t[2])
        out.append(f"clone {dx} {dy} {dz} {ex} {ey} {ez} {t[0]} {t[1]} {t[2]} replace force")
    return out


def clear_commands(box: Box) -> list[str]:
    """Fill the box with air, tiled to <= 32768 blocks per command."""
    return [f"fill {t[0]} {t[1]} {t[2]} {t[3]} {t[4]} {t[5]} air" for t in _tiles(box)]


def forceload_commands(box: Box, add: bool) -> list[str]:
    """forceload add/remove covering every chunk the box touches (chunk = block // 16)."""
    x0, y0, z0, x1, y1, z1 = _norm(box)
    cx0, cx1 = x0 // 16, x1 // 16
    cz0, cz1 = z0 // 16, z1 // 16
    verb = "add" if add else "remove"
    out = []
    for cz in range(cz0, cz1 + 1, _MAX_FORCELOAD_CHUNKS):
        for cx in range(cx0, cx1 + 1, _MAX_FORCELOAD_CHUNKS):
            ex = min(cx + _MAX_FORCELOAD_CHUNKS - 1, cx1)
            ez = min(cz + _MAX_FORCELOAD_CHUNKS - 1, cz1)
            out.append(f"forceload {verb} {cx * 16} {cz * 16} {ex * 16} {ez * 16}")
    return out


def say(msg: str) -> str:
    """A gold tellraw broadcast with `msg` JSON-escaped."""
    return "tellraw @a " + json.dumps({"text": msg, "color": "gold"}, separators=(",", ":"))


def build_commands(vox: Voxels, slot: int) -> list[str]:
    """Force-load, back up the site, place every block, then release the chunks.

    The backup lands at the storage box for `slot` (see `storage_box`, origin
    `(100000 + slot*256, 200, 100000)`); both the site box and the storage box
    are force-loaded for the duration.
    """
    box = bounds(vox)
    store = storage_box(box, slot)
    out = forceload_commands(box, add=True) + forceload_commands(store, add=True)
    out += backup_commands(box, slot)
    out += to_commands(vox)
    out += forceload_commands(store, add=False) + forceload_commands(box, add=False)
    return out


def undo_commands(box: Box, slot: int) -> list[str]:
    """Force-load, restore the site from the storage backup for `slot`, then release."""
    store = storage_box(box, slot)
    out = forceload_commands(box, add=True) + forceload_commands(store, add=True)
    out += restore_commands(box, slot)
    out += forceload_commands(store, add=False) + forceload_commands(box, add=False)
    return out
