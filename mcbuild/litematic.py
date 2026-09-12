"""Litematica (.litematic) reader -> sparse voxel dict.

Voxel dict convention used across mcbuild: {(x, y, z): "block_name[prop=val,...]"}
Air is never stored.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import nbtlib
import numpy as np

Voxels = dict[tuple[int, int, int], str]


@dataclass
class Region:
    name: str
    size: tuple[int, int, int]  # x, y, z (positive)
    palette: list[str]
    index: np.ndarray  # shape (y, z, x), palette indices

    def voxels(self) -> Voxels:
        out: Voxels = {}
        air = {i for i, p in enumerate(self.palette) if p == "air"}
        ys, zs, xs = np.nonzero(~np.isin(self.index, list(air)))
        for y, z, x in zip(ys, zs, xs):
            out[(int(x), int(y), int(z))] = self.palette[self.index[y, z, x]]
        return out


def _palette_entry(p) -> str:
    name = str(p["Name"]).removeprefix("minecraft:")
    props = p.get("Properties")
    if props:
        name += "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]"
    return name


def load(path: str | Path) -> list[Region]:
    root = nbtlib.load(str(path), gzipped=True)
    regions = []
    for rname, r in root["Regions"].items():
        size = tuple(abs(int(r["Size"][k])) for k in "xyz")
        palette = [_palette_entry(p) for p in r["BlockStatePalette"]]
        bits = max(2, math.ceil(math.log2(len(palette))))
        longs = np.array(r["BlockStates"], dtype=np.int64).astype(np.uint64)
        n = size[0] * size[1] * size[2]
        bitarr = np.unpackbits(longs.view(np.uint8), bitorder="little")[: n * bits].reshape(n, bits)
        idx = np.zeros(n, dtype=np.int64)
        for b in range(bits):
            idx |= bitarr[:, b].astype(np.int64) << b
        regions.append(Region(rname, size, palette, idx.reshape(size[1], size[2], size[0])))
    return regions


def load_voxels(path: str | Path) -> Voxels:
    """Merge all regions (positions ignored: reference schematics here are single-region)."""
    vox: Voxels = {}
    for r in load(path):
        vox.update(r.voxels())
    return vox
