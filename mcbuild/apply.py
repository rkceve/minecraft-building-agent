"""Persistent build state and diff-based application to the live server.

Slot allocation: `slot = (crc32(build_id) % 200) + 1`. Slots are storage
*regions* on the server (see `emit.storage_box`/`emit.backup_commands`), not
files -- each build_id gets a stable region at
`(100000 + slot*256, 200, 100000)` where its pre-build backup is cloned to.
"""
from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from . import emit
from .litematic import Voxels

STATE_DIR = Path("state")


@dataclass
class BuildState:
    build_id: str
    origin: tuple[int, int, int]
    voxels: Voxels
    provenance: dict[tuple[int, int, int], str]
    script_path: str
    slot: int
    # The box actually cloned into storage at first apply (None if the build
    # was applied with first_time_backup=False, so no backup exists at all).
    # Carried forward unchanged on every later apply -- backups are never
    # extended, so voxels placed outside this box on a later apply have no
    # backup copy (see `undo_build`).
    backup_box: tuple[int, int, int, int, int, int] | None = None


@dataclass
class ApplyResult:
    added: int
    removed: int
    commands: int
    ok: int
    failed: list[tuple[str, str]] = field(default_factory=list)
    seconds: float = 0.0


def slot_for(build_id: str) -> int:
    """Stable storage slot for a build id (slots are storage regions, see module docstring)."""
    return (zlib.crc32(build_id.encode()) % 200) + 1


def _state_path(build_id: str) -> Path:
    return STATE_DIR / f"{build_id}.json"


def load_state(build_id: str) -> BuildState | None:
    path = _state_path(build_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    voxels: Voxels = {(x, y, z): block for x, y, z, block in data["voxels"]}
    provenance = {(x, y, z): eid for x, y, z, eid in data["provenance"]}
    backup_box = data.get("backup_box")
    return BuildState(
        build_id=data["build_id"],
        origin=tuple(data["origin"]),
        voxels=voxels,
        provenance=provenance,
        script_path=data["script_path"],
        slot=data["slot"],
        backup_box=tuple(backup_box) if backup_box is not None else None,
    )


def save_state(st: BuildState) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "build_id": st.build_id,
        "origin": list(st.origin),
        "voxels": [[x, y, z, block] for (x, y, z), block in st.voxels.items()],
        "provenance": [[x, y, z, eid] for (x, y, z), eid in st.provenance.items()],
        "script_path": st.script_path,
        "slot": st.slot,
        "backup_box": list(st.backup_box) if st.backup_box is not None else None,
    }
    _state_path(st.build_id).write_text(json.dumps(data))


def diff(old: Voxels, new: Voxels) -> tuple[Voxels, set[tuple[int, int, int]]]:
    """(changed_or_added, removed): positions in `new` that are new or differ from `old`,
    and positions in `old` no longer present in `new`."""
    changed_or_added: Voxels = {}
    for pos, block in new.items():
        if old.get(pos) != block:
            changed_or_added[pos] = block
    removed = {pos for pos in old if pos not in new}
    return changed_or_added, removed


def _bbox(positions: set[tuple[int, int, int]]) -> emit.Box:
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def apply_build(build_id: str, dump_json: str, cfg, rate: float = 0, first_time_backup: bool = True) -> ApplyResult:
    """Apply a preview JSON dump to the live build, diffed against saved state.

    On first apply for `build_id` (no saved state) a `/clone` backup of the
    site box is taken before placing anything, unless `first_time_backup` is
    False. That box is recorded as `BuildState.backup_box` and carried
    forward unchanged on every later apply -- the backup is never re-taken
    or extended. If a later apply places voxels outside `backup_box`,
    `undo_build` cannot restore whatever used to be there (there is no
    backup of it); the best it can do is clear those voxels back to air.
    This is "correct enough for a flat world" (ground is air below y=1
    everywhere) but is a real limitation on worlds with pre-existing
    structure outside the original footprint. State is only saved if every
    command succeeded.
    """
    from . import runner

    with open(dump_json, encoding="utf-8") as fh:
        dump = json.load(fh)
    new_voxels: Voxels = {(x, y, z): block for x, y, z, block in dump["voxels"]}
    new_provenance = {(x, y, z): eid for x, y, z, eid in dump["provenance"]}

    old_state = load_state(build_id)
    old_voxels: Voxels = old_state.voxels if old_state is not None else {}
    is_first_apply = old_state is None

    changed, removed = diff(old_voxels, new_voxels)

    slot = slot_for(build_id)
    all_positions = set(old_voxels) | set(new_voxels)
    cmds: list[str] = []
    backup_box = old_state.backup_box if old_state is not None else None
    if all_positions:
        box = _bbox(all_positions)
        cmds += emit.forceload_commands(box, add=True)
        if is_first_apply and first_time_backup:
            # Nothing exists at this box yet; back it up anyway so undo has a
            # known (empty-site) backup to restore to.
            store = emit.storage_box(box, slot)
            cmds += emit.forceload_commands(store, add=True)
            cmds += emit.backup_commands(box, slot)
            cmds += emit.forceload_commands(store, add=False)
            backup_box = box

        if removed:
            removed_air: Voxels = {pos: "air" for pos in removed}
            cmds += emit.to_commands(removed_air)
        if changed:
            cmds += emit.to_commands(changed)
        cmds += emit.forceload_commands(box, add=False)

    result = runner.run_commands(cmds, cfg, rate=rate)

    if not result.failed:
        save_state(
            BuildState(
                build_id=build_id,
                origin=tuple(dump.get("origin", (0, 0, 0))),
                voxels=new_voxels,
                provenance=new_provenance,
                script_path=dump.get("script_path", dump_json),
                slot=slot,
                backup_box=backup_box,
            )
        )

    return ApplyResult(
        added=len(changed),
        removed=len(removed),
        commands=len(cmds),
        ok=result.ok,
        failed=result.failed,
        seconds=result.seconds,
    )


def _in_box(pos: tuple[int, int, int], box: emit.Box) -> bool:
    x0, y0, z0, x1, y1, z1 = box
    x, y, z = pos
    return x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1


def undo_build(build_id: str, cfg) -> ApplyResult:
    """Restore the pre-build backup for `build_id` and delete its saved state.

    Only `backup_box` (the region actually cloned at first apply) can be
    restored via `emit.undo_commands`. Any current voxel outside
    `backup_box` -- placed by a later apply that grew past the original
    footprint -- has no backup to restore, so it is simply cleared to air
    instead (see `apply_build` docstring).
    """
    from . import runner

    st = load_state(build_id)
    if st is None:
        return ApplyResult(added=0, removed=0, commands=0, ok=0, failed=[(build_id, "no saved state")], seconds=0.0)

    cmds: list[str] = []
    if st.backup_box is not None:
        cmds += emit.undo_commands(st.backup_box, st.slot)
        outside = {pos for pos in st.voxels if not _in_box(pos, st.backup_box)}
    else:
        outside = set(st.voxels)

    if outside:
        outside_box = _bbox(outside)
        cmds += emit.forceload_commands(outside_box, add=True)
        cmds += emit.to_commands({pos: "air" for pos in outside})
        cmds += emit.forceload_commands(outside_box, add=False)

    result = runner.run_commands(cmds, cfg)

    if not result.failed:
        _state_path(build_id).unlink(missing_ok=True)

    return ApplyResult(
        added=0,
        removed=len(st.voxels),
        commands=len(cmds),
        ok=result.ok,
        failed=result.failed,
        seconds=result.seconds,
    )


def _cli(argv: list[str] | None = None) -> int:
    import argparse

    from . import runner

    ap = argparse.ArgumentParser(description="Apply or undo a build against the live server.")
    ap.add_argument("--id", required=True, dest="build_id", help="build id")
    ap.add_argument("--json", help="preview JSON dump path (required unless --undo)")
    ap.add_argument("--rate", type=float, default=0, help="max commands/sec")
    ap.add_argument("--undo", action="store_true", help="undo a previously applied build")
    args = ap.parse_args(argv)

    cfg = runner.load_config()
    if args.undo:
        result = undo_build(args.build_id, cfg)
    else:
        if not args.json:
            ap.error("--json is required unless --undo")
        result = apply_build(args.build_id, args.json, cfg, rate=args.rate)

    print(
        f"added={result.added} removed={result.removed} commands={result.commands} "
        f"ok={result.ok} failed={len(result.failed)} in {result.seconds:.1f}s"
    )
    for cmd, response in result.failed:
        print(f"FAIL\t{cmd}\t{response}")
    return 1 if result.failed else 0


if __name__ == "__main__":
    import sys

    sys.exit(_cli())
