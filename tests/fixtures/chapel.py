"""Reference chapel script: a small 15x25 chapel with pointed windows, a rose window on
the front gable, a centred door, buttresses, a gable roof (ridge along z) and a floor.
"""
from __future__ import annotations

from mcbuild.dsl import Build
from mcbuild.palette import Palette


def build() -> Build:
    b = Build(origin=(0, 1, 0), palette=Palette(), seed=42)

    x0, z0, x1, z1 = 0, 0, 14, 24
    y0 = 1
    height = 12

    frames = b.room(x0, z0, x1, z1, y0, height, thickness=1, plinth=True)

    b.beam(x0, 8, x1, 8, y0 + 8, id="nave_beam")

    for face in ("e", "w"):
        frame = frames[face]
        count, width = 3, 3
        b.windows(frame, v=3, width=width, height=7, count=count, id=f"window_{face}")

        total_gap = frame.width - count * width
        gap = total_gap // (count + 1)
        remainder = total_gap - gap * (count + 1)
        left_extra = remainder // 2
        u = gap + left_extra
        boundary_us = [u - 1]
        for _ in range(count):
            boundary_us.append(u + width + 1)
            u += width + gap
        for i, bu in enumerate(boundary_us):
            bu = max(0, min(frame.width - 2, bu))
            b.buttress(frame, bu, id=f"buttress_{face}_{i}")

    front = frames["s"]
    b.window(front, u=(front.width - 5) // 2, v=height - 6, width=5, height=5, style="rose", id="rose_window")
    b.door(front, id="front_door")

    b.gable_roof(x0, z0, x1, z1, y0 + height + 1, ridge="z", overhang=1)

    b.floor(x0, z0, x1, z1, y0 - 1)

    return b
