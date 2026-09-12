"""CLI preview for a build.py script.

    python -m mcbuild.preview build.py [--faces n,s,e,w] [--json out.json]

`build.py` must define `def build() -> Build`.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from .ascii import elevation
from .dsl import Build
from .emit import bounds


def _load_build(path: Path) -> Build:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise AttributeError(f"{path} does not define build()")
    return module.build()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview a mcbuild build.py script")
    parser.add_argument("script", type=Path)
    parser.add_argument("--faces", default="n,s,e,w")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    build = _load_build(args.script)
    vox = build.voxels()
    prov = build.provenance()

    print(f"blocks: {len(vox)}")
    print(f"palette: {build.palette}")
    if vox:
        x0, y0, z0, x1, y1, z1 = bounds(vox)
        print(f"bounds: ({x0},{y0},{z0}) .. ({x1},{y1},{z1})")

    print("elements:")
    for eid, meta in build.elements().items():
        print(f"  {eid}: {meta['kind']} bbox={meta['bbox']}")

    warnings = build.check()
    print(f"check(): {len(warnings)} warning(s)")
    for w in warnings:
        print(f"  ! {w}")

    faces = [f.strip() for f in args.faces.split(",") if f.strip()]
    for face in faces:
        print(f"\n=== elevation {face} ===")
        print(elevation(vox, face))

    if args.json:
        payload = {
            "voxels": [[x, y, z, b] for (x, y, z), b in vox.items()],
            "provenance": [[x, y, z, eid] for (x, y, z), eid in prov.items()],
            "elements": build.elements(),
        }
        args.json.write_text(json.dumps(payload), encoding="utf-8")
        print(f"\nwrote {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
