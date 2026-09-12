"""ASCII elevations of voxel dicts, for humans and for the design LLM."""
from __future__ import annotations

from .litematic import Voxels

_SYMBOLS = [
    ("air", "."), ("glass", "g"), ("stairs", "/"), ("slab", "-"), ("wall", "w"),
    ("fence", "f"), ("trapdoor", "t"), ("end_rod", "|"), ("froglight", "o"),
    ("lantern", "*"), ("door", "D"), ("log", "L"), ("planks", "p"), ("bricks", "B"),
]


def symbol(block: str) -> str:
    base = block.split("[")[0]
    if base == "air":
        return "."
    for key, sym in _SYMBOLS:
        if key == "air":
            continue  # "air" is a substring of "stairs"; handled by the exact check above
        if key in base:
            if key == "stairs" and "half=top" in block:
                return "\\"
            if key == "slab" and "type=top" in block:
                return "^"
            return sym
    return "#"


def elevation(vox: Voxels, face: str, bounds=None) -> str:
    """Project voxels onto a wall face. face in n/s/e/w. Nearest block along the view axis wins."""
    if not vox:
        return ""
    xs = [p[0] for p in vox]
    ys = [p[1] for p in vox]
    zs = [p[2] for p in vox]
    x0, x1, y0, y1, z0, z1 = bounds or (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    lines = []
    for y in range(y1, y0 - 1, -1):
        row = []
        if face in ("n", "s"):
            cols = range(x0, x1 + 1) if face == "s" else range(x1, x0 - 1, -1)
            depth = range(z1, z0 - 1, -1) if face == "s" else range(z0, z1 + 1)
            for x in cols:
                c = "."
                for z in depth:
                    b = vox.get((x, y, z))
                    if b:
                        c = symbol(b)
                        break
                row.append(c)
        else:
            cols = range(z0, z1 + 1) if face == "w" else range(z1, z0 - 1, -1)
            depth = range(x0, x1 + 1) if face == "w" else range(x1, x0 - 1, -1)
            for z in cols:
                c = "."
                for x in depth:
                    b = vox.get((x, y, z))
                    if b:
                        c = symbol(b)
                        break
                row.append(c)
        lines.append(f"{y:4d} " + "".join(row))
    return "\n".join(lines)
