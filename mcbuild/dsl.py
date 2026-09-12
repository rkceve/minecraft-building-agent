"""The Build API Astra (the design LLM) imports to compose a script into voxels.

All coordinates passed to `Build` methods are local (relative to `origin`); `Build.voxels()`
and `Build.provenance()` return world coordinates with `origin` applied.
"""
from __future__ import annotations

from . import blockstate as bs
from . import techniques as tq
from .litematic import Voxels
from .palette import Palette

Point3 = tuple[int, int, int]
Box = tuple[int, int, int, int, int, int]


def _bbox(vox: Voxels) -> Box:
    if not vox:
        return (0, 0, 0, 0, 0, 0)
    xs = [p[0] for p in vox]
    ys = [p[1] for p in vox]
    zs = [p[2] for p in vox]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def _boxes_overlap(a: Box, b: Box) -> bool:
    ax0, ay0, az0, ax1, ay1, az1 = a
    bx0, by0, bz0, bx1, by1, bz1 = b
    return ax0 <= bx1 and bx0 <= ax1 and ay0 <= by1 and by0 <= ay1 and az0 <= bz1 and bz0 <= az1


class Build:
    def __init__(self, origin: Point3 = (0, 1, 0), palette: Palette | None = None, seed: int = 0) -> None:
        self.origin = origin
        self.palette = palette or Palette()
        self.seed = seed
        self._order: list[str] = []
        self._vox: dict[str, Voxels] = {}
        self._meta: dict[str, dict] = {}
        self._counters: dict[str, int] = {}
        self._frames: dict[str, tq.Frame] = {}
        self._footprint_checks: list[tuple[str, int]] = []

    # -- bookkeeping -------------------------------------------------
    def _next_id(self, kind: str) -> str:
        n = self._counters.get(kind, 0) + 1
        self._counters[kind] = n
        return f"{kind}_{n}"

    def _add(self, kind: str, vox: Voxels, args: dict, id: str | None = None) -> str:
        eid = id or self._next_id(kind)
        self._order.append(eid)
        self._vox[eid] = vox
        self._meta[eid] = {"kind": kind, "args": args, "bbox": _bbox(vox)}
        return eid

    # -- raw -----------------------------------------------------------
    def box(self, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int, block: str, id: str | None = None) -> None:
        vox = {
            (x, y, z): block
            for x in range(min(x0, x1), max(x0, x1) + 1)
            for y in range(min(y0, y1), max(y0, y1) + 1)
            for z in range(min(z0, z1), max(z0, z1) + 1)
        }
        self._add("box", vox, {"x0": x0, "y0": y0, "z0": z0, "x1": x1, "y1": y1, "z1": z1, "block": block}, id)

    def put(self, x: int, y: int, z: int, block: str, id: str | None = None) -> None:
        self._add("put", {(x, y, z): block}, {"x": x, "y": y, "z": z, "block": block}, id)

    def clear(self, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int) -> None:
        vox = {
            (x, y, z): tq.AIR
            for x in range(min(x0, x1), max(x0, x1) + 1)
            for y in range(min(y0, y1), max(y0, y1) + 1)
            for z in range(min(z0, z1), max(z0, z1) + 1)
        }
        self._add("clear", vox, {"x0": x0, "y0": y0, "z0": z0, "x1": x1, "y1": y1, "z1": z1})

    # -- elements --------------------------------------------------------
    def wall(
        self,
        face: str,
        x0: int,
        z0: int,
        x1: int,
        z1: int,
        y0: int,
        height: int,
        thickness: int = 1,
        depth: bool = True,
        bay: int = 6,
        id: str | None = None,
    ) -> tq.Frame:
        if face in ("n", "s"):
            if z0 != z1:
                raise ValueError("wall on n/s face must have z0 == z1")
            width = abs(x1 - x0) + 1
            frame_z0 = z0
            frame_x0 = max(x0, x1) if face == "n" else min(x0, x1)
        elif face in ("e", "w"):
            if x0 != x1:
                raise ValueError("wall on e/w face must have x0 == x1")
            width = abs(z1 - z0) + 1
            frame_x0 = x0
            frame_z0 = max(z0, z1) if face == "e" else min(z0, z1)
        else:
            raise ValueError(f"unknown face {face!r}")

        frame = tq.Frame(face, frame_x0, y0, frame_z0, width, height, thickness)
        vox = tq.wall_fill(frame, self.palette, thickness)
        if depth:
            vox.update(tq.wall_depth(frame, self.palette, bay))
        eid = self._add(
            "wall",
            vox,
            {"face": face, "x0": x0, "z0": z0, "x1": x1, "z1": z1, "y0": y0, "height": height, "thickness": thickness},
            id,
        )
        self._frames[eid] = frame
        return frame

    def window(
        self,
        frame: tq.Frame,
        u: int,
        v: int,
        width: int,
        height: int,
        style: str = "pointed",
        mullion: bool = True,
        id: str | None = None,
    ) -> None:
        vox = tq.window_frame(frame, u, v, width, height, self.palette, style=style, mullion=mullion)
        self._add("window", vox, {"u": u, "v": v, "width": width, "height": height, "style": style}, id)

    def windows(
        self,
        frame: tq.Frame,
        v: int,
        width: int,
        height: int,
        count: int,
        style: str = "pointed",
        id: str | None = None,
    ) -> None:
        total_gap = frame.width - count * width
        gap = total_gap // (count + 1)
        remainder = total_gap - gap * (count + 1)
        left_extra = remainder // 2
        u = gap + left_extra
        for i in range(count):
            wid = f"{id}_{i}" if id else None
            self.window(frame, u, v, width, height, style=style, id=wid)
            u += width + gap

    def door(
        self, frame: tq.Frame, u: int | None = None, width: int = 2, height: int = 3, id: str | None = None
    ) -> None:
        if u is None:
            u = (frame.width - width) // 2
        vox = tq.door_opening(frame, self.palette, u, width=width, height=height)
        self._add("door", vox, {"u": u, "width": width, "height": height}, id)

    def corner_pillar(self, x: int, z: int, y0: int, height: int, size: int = 3, id: str | None = None) -> None:
        vox = tq.corner_pillar(x, z, y0, height, self.palette, size=size)
        self._add("corner_pillar", vox, {"x": x, "z": z, "y0": y0, "height": height, "size": size}, id)

    def buttress(
        self, frame: tq.Frame, u: int, depth: int = 3, height: int | None = None, id: str | None = None
    ) -> None:
        vox = tq.buttress(frame, self.palette, u, depth=depth, height=height)
        self._add("buttress", vox, {"u": u, "depth": depth, "height": height}, id)

    def eave(self, frame: tq.Frame, overhang: int = 1, id: str | None = None) -> None:
        vox = tq.eave(frame, self.palette, overhang=overhang)
        self._add("eave", vox, {"face": frame.face, "overhang": overhang}, id)

    def gable_roof(
        self,
        x0: int,
        z0: int,
        x1: int,
        z1: int,
        y_base: int,
        ridge: str = "x",
        overhang: int = 1,
        id: str | None = None,
    ) -> None:
        vox = tq.gable_roof(x0, z0, x1, z1, y_base, self.palette, ridge=ridge, overhang=overhang)
        self._add("gable_roof", vox, {"x0": x0, "z0": z0, "x1": x1, "z1": z1, "y_base": y_base, "ridge": ridge}, id)

    def spire(
        self, x0: int, z0: int, x1: int, z1: int, y_base: int, height: int, id: str | None = None
    ) -> None:
        vox = tq.spire(x0, z0, x1, z1, y_base, self.palette, height)
        self._add("spire", vox, {"x0": x0, "z0": z0, "x1": x1, "z1": z1, "y_base": y_base, "height": height}, id)

    def floor(self, x0: int, z0: int, x1: int, z1: int, y: int, id: str | None = None) -> None:
        vox = tq.floor_texture(x0, z0, x1, z1, y, self.palette, seed=self.seed)
        self._add("floor", vox, {"x0": x0, "z0": z0, "x1": x1, "z1": z1, "y": y}, id)

    def plinth(
        self,
        x0: int,
        z0: int,
        x1: int,
        z1: int,
        y0: int,
        height: int | None = None,
        projection: int = 1,
        id: str | None = None,
    ) -> None:
        vox = tq.plinth(x0, z0, x1, z1, y0, self.palette, height=height, projection=projection)
        self._add(
            "plinth",
            vox,
            {"x0": x0, "z0": z0, "x1": x1, "z1": z1, "y0": y0, "height": height, "projection": projection},
            id,
        )

    def beam(
        self, x0: int, z0: int, x1: int, z1: int, y: int, braces: bool = True, id: str | None = None
    ) -> None:
        vox = tq.beam(x0, z0, x1, z1, y, self.palette, braces=braces)
        self._add("beam", vox, {"x0": x0, "z0": z0, "x1": x1, "z1": z1, "y": y, "braces": braces}, id)

    # -- composites --------------------------------------------------------
    def room(
        self,
        x0: int,
        z0: int,
        x1: int,
        z1: int,
        y0: int,
        height: int,
        thickness: int = 1,
        pillars: bool = True,
        eaves: bool = True,
        plinth: bool = True,
        id: str | None = None,
    ) -> dict[str, tq.Frame]:
        base = id or self._next_id("room")
        width = abs(x1 - x0) + 1
        self._footprint_checks.append((base, width))
        frames: dict[str, tq.Frame] = {}

        if plinth:
            self.plinth(x0, z0, x1, z1, y0, id=f"{base}_plinth")

        frames["n"] = self.wall("n", x0, z0, x1, z0, y0, height, thickness, id=f"{base}_wall_n")
        frames["s"] = self.wall("s", x0, z1, x1, z1, y0, height, thickness, id=f"{base}_wall_s")
        frames["e"] = self.wall("e", x1, z0, x1, z1, y0, height, thickness, id=f"{base}_wall_e")
        frames["w"] = self.wall("w", x0, z0, x0, z1, y0, height, thickness, id=f"{base}_wall_w")

        if pillars:
            size = 3
            corners = [
                (x0, z0, 1, 1),
                (x1, z0, -1, 1),
                (x0, z1, 1, -1),
                (x1, z1, -1, -1),
            ]
            for cx, cz, sx, sz in corners:
                min_x = cx if sx > 0 else cx - size + 1
                min_z = cz if sz > 0 else cz - size + 1
                self.corner_pillar(min_x, min_z, y0, height + 1, size=size, id=f"{base}_pillar_{cx}_{cz}")

        if eaves:
            for face, frame in frames.items():
                self.eave(frame, id=f"{base}_eave_{face}")

        return frames

    def tower(
        self,
        x0: int,
        z0: int,
        x1: int,
        z1: int,
        y0: int,
        height: int,
        spire_height: int | None = None,
        id: str | None = None,
    ) -> dict[str, tq.Frame]:
        base = id or self._next_id("tower")
        frames = self.room(x0, z0, x1, z1, y0, height, eaves=False, id=base)
        span = max(x1 - x0 + 1, z1 - z0 + 1)
        sh = spire_height if spire_height is not None else span
        self.spire(x0, z0, x1, z1, y0 + height, sh, id=f"{base}_spire")
        return frames

    # -- output --------------------------------------------------------
    def voxels(self) -> Voxels:
        master: Voxels = {}
        prov: dict[Point3, str] = {}
        for eid in self._order:
            for pos, block in self._vox[eid].items():
                master[pos] = block
                prov[pos] = eid

        bs.connect_fences_and_walls(master)
        bs.fix_stair_corners(master)

        ox, oy, oz = self.origin
        out: Voxels = {}
        self._last_prov: dict[Point3, str] = {}
        for pos, block in master.items():
            if block == tq.AIR:
                continue
            wpos = (pos[0] + ox, pos[1] + oy, pos[2] + oz)
            out[wpos] = block
            self._last_prov[wpos] = prov[pos]
        return out

    def provenance(self) -> dict[Point3, str]:
        if not hasattr(self, "_last_prov"):
            self.voxels()
        return self._last_prov

    def elements(self) -> dict[str, dict]:
        return dict(self._meta)

    def check(self) -> list[str]:
        warnings: list[str] = []
        vox = self.voxels()
        if not vox:
            return warnings
        positions = set(vox.keys())

        for pos, block in vox.items():
            x, y, z = pos
            neighbours = ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1))
            if not any(n in positions for n in neighbours):
                warnings.append(f"floating block at {pos}: {block}")

        window_ids = [eid for eid, m in self._meta.items() if m["kind"] == "window"]
        pillar_ids = [eid for eid, m in self._meta.items() if m["kind"] == "corner_pillar"]
        for wid in window_ids:
            w_positions = set(self._vox[wid].keys())
            for pid in pillar_ids:
                if not _boxes_overlap(self._meta[wid]["bbox"], self._meta[pid]["bbox"]):
                    continue
                if w_positions & set(self._vox[pid].keys()):
                    warnings.append(f"window {wid} overlaps pillar {pid}")

        xs = [p[0] for p in vox]
        ys = [p[1] for p in vox]
        zs = [p[2] for p in vox]
        if max(xs) - min(xs) > 64 or max(ys) - min(ys) > 64 or max(zs) - min(zs) > 64:
            warnings.append("build exceeds 64x64x64 envelope")

        for name, width in self._footprint_checks:
            if width % 2 == 0:
                warnings.append(f"builder's rule: widths should be odd ({name} is {width} wide)")

        return warnings
