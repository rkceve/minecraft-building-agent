"""Inspect a voxel-generator module and optionally stream it to the demo server.

    python -m experiments.push experiments/plain_astra/church_plain.py --origin 0 0 0 [--send --rate 40] [--undo]
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcbuild import emit, runner  # noqa: E402
from mcbuild.ascii import elevation  # noqa: E402


def load_build(path: str):
    spec = importlib.util.spec_from_file_location("gen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--origin", nargs=3, type=int, default=[0, 0, 0])
    ap.add_argument("--slot", type=int, default=1)
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--rate", type=int, default=0)
    ap.add_argument("--undo", action="store_true")
    ap.add_argument("--faces", default="n,e")
    a = ap.parse_args()

    vox = load_build(a.file)
    ox, oy, oz = a.origin
    vox = {(x + ox, y + oy, z + oz): b for (x, y, z), b in vox.items()}
    box = emit.bounds(vox)
    print("blocks", len(vox), "box", box)
    for name, n in Counter(b.split("[")[0] for b in vox.values()).most_common(15):
        print(f"{n:6d} {name}")
    for f in a.faces.split(","):
        print(f"=== elevation {f}")
        print(elevation(vox, f))

    cfg = runner.load_config()
    if a.undo:
        r = runner.run_commands(emit.undo_commands(box, a.slot), cfg)
        print("undo:", r.ok, "ok", len(r.failed), "failed", f"{r.seconds:.1f}s", r.failed[:5])
        return 0
    if a.send:
        cmds = emit.build_commands(vox, a.slot)
        print("commands", len(cmds))
        r = runner.run_commands(cmds, cfg, rate=a.rate) if a.rate else runner.run_commands(cmds, cfg)
        print("build:", r.ok, "ok", len(r.failed), "failed", f"{r.seconds:.1f}s", r.failed[:5])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
