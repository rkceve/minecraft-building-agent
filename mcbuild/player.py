"""Player pose lookup, view geometry, and voxel raycasting.

`get_pose` reads the live player state over RCON (via `runner.rcon_one`).
Everything else here is pure geometry so it can be unit tested without a
server.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .litematic import Voxels

_POS_RE = re.compile(r"\[([^\]]+)\]")


@dataclass
class Pose:
    x: float
    y: float
    z: float
    yaw: float
    pitch: float


def _parse_triplet(text: str) -> list[float] | None:
    """Parse a `data get` response like '<name> has the following entity data: [1.5d, 2.0d, -3.2d]'."""
    m = _POS_RE.search(text)
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split(",") if p.strip()]
    try:
        return [float(p.rstrip("dDfF")) for p in parts]
    except ValueError:
        return None


def get_pose(name: str, cfg) -> Pose | None:
    """Fetch a player's position and rotation over RCON.

    Returns None if the player is offline (no entity data in the response).
    """
    from . import runner

    pos_text = runner.rcon_one(f"data get entity {name} Pos", cfg)
    pos = _parse_triplet(pos_text)
    if pos is None or len(pos) != 3:
        return None
    rot_text = runner.rcon_one(f"data get entity {name} Rotation", cfg)
    rot = _parse_triplet(rot_text)
    if rot is None or len(rot) != 2:
        return None
    x, y, z = pos
    yaw, pitch = rot
    return Pose(x=x, y=y, z=z, yaw=yaw, pitch=pitch)


def view_vector(pose: Pose) -> tuple[float, float, float]:
    """Minecraft yaw/pitch (degrees) -> unit look direction.

    yaw 0 = +z (south), yaw 90 = -x (west); pitch 90 = looking straight down (-y).
    """
    yaw_r = math.radians(pose.yaw)
    pitch_r = math.radians(pose.pitch)
    x = -math.sin(yaw_r) * math.cos(pitch_r)
    y = -math.sin(pitch_r)
    z = math.cos(yaw_r) * math.cos(pitch_r)
    return (x, y, z)


def eye(pose: Pose) -> tuple[float, float, float]:
    """Eye position: standing feet position + 1.62 (Minecraft player eye height)."""
    return (pose.x, pose.y + 1.62, pose.z)


def raycast(
    vox: Voxels, origin: tuple[float, float, float], direction: tuple[float, float, float], max_dist: float = 64.0
) -> tuple[int, int, int] | None:
    """Voxel DDA (Amanatides-Woo): first voxel key present in `vox` along the ray.

    `origin` and `direction` are world-space floats; `direction` need not be
    normalized (but should be non-zero).
    """
    ox, oy, oz = origin
    dx, dy, dz = direction
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length == 0:
        return None
    dx, dy, dz = dx / length, dy / length, dz / length

    x, y, z = math.floor(ox), math.floor(oy), math.floor(oz)

    def _axis(o: float, d: float, cell: int) -> tuple[int, float, float]:
        if d > 0:
            return 1, (cell + 1 - o) / d, 1.0 / d
        elif d < 0:
            return -1, (cell - o) / d, -1.0 / d
        else:
            return 0, math.inf, math.inf

    step_x, t_max_x, t_delta_x = _axis(ox, dx, x)
    step_y, t_max_y, t_delta_y = _axis(oy, dy, y)
    step_z, t_max_z, t_delta_z = _axis(oz, dz, z)

    traveled = 0.0
    while traveled <= max_dist:
        if (x, y, z) in vox:
            return (x, y, z)
        if t_max_x < t_max_y and t_max_x < t_max_z:
            x += step_x
            traveled = t_max_x
            t_max_x += t_delta_x
        elif t_max_y < t_max_z:
            y += step_y
            traveled = t_max_y
            t_max_y += t_delta_y
        else:
            z += step_z
            traveled = t_max_z
            t_max_z += t_delta_z
    return None


def ground_target(pose: Pose, max_dist: float = 48.0, ground_y: int = 0) -> tuple[int, int, int] | None:
    """Where the view ray crosses the plane y = ground_y + 1 (top of ground), floored.

    Returns None if the ray is looking level or upward (never reaches the plane).
    """
    ox, oy, oz = eye(pose)
    dx, dy, dz = view_vector(pose)
    plane_y = ground_y + 1
    if dy >= 0:
        return None
    t = (plane_y - oy) / dy
    if t < 0 or t > max_dist:
        return None
    x = ox + dx * t
    z = oz + dz * t
    return (math.floor(x), plane_y, math.floor(z))


_CARDINALS = [(0.0, "s"), (90.0, "w"), (180.0, "n"), (270.0, "e")]


def _facing_cardinal(yaw: float) -> str:
    yaw = yaw % 360.0
    best = min(_CARDINALS, key=lambda d: min(abs(yaw - d[0]), 360.0 - abs(yaw - d[0])))
    return best[1]


def describe_context(pose: Pose, state: "BuildState | None") -> str:  # noqa: F821 - forward ref, see apply.py
    """Human-readable lines describing the player's position and view for the LLM prompt."""
    lines = []
    lines.append(f"Player position: ({int(pose.x)}, {int(pose.y)}, {int(pose.z)})")
    lines.append(f"Facing: {_facing_cardinal(pose.yaw)} (yaw={pose.yaw:.1f}, pitch={pose.pitch:.1f})")

    origin = eye(pose)
    direction = view_vector(pose)
    hit = None
    if state is not None and state.voxels:
        hit = raycast(state.voxels, origin, direction)
    if hit is not None:
        block = state.voxels.get(hit, "?")
        elem = state.provenance.get(hit) if state.provenance else None
        if elem is not None:
            lines.append(f"Looking at: {block} at {hit} (element: {elem})")
        else:
            lines.append(f"Looking at: {block} at {hit}")
    else:
        lines.append("Looking at: nothing built yet")

    ground = ground_target(pose)
    if ground is not None:
        lines.append(f"Ground target (line of sight hits ground at): {ground}")
    else:
        lines.append("Ground target: none (looking level or upward)")
    return "\n".join(lines)


def _cli(argv: list[str] | None = None) -> int:
    import argparse

    from . import runner
    from .apply import STATE_DIR, BuildState, load_state

    ap = argparse.ArgumentParser(description="Describe a player's position and view.")
    ap.add_argument("--name", required=True, help="player name")
    args = ap.parse_args(argv)

    cfg = runner.load_config()
    pose = get_pose(args.name, cfg)
    if pose is None:
        print(f"{args.name} is not online.")
        return 1

    merged_voxels: Voxels = {}
    merged_provenance: dict[tuple[int, int, int], str] = {}
    if STATE_DIR.exists():
        for path in STATE_DIR.glob("*.json"):
            st = load_state(path.stem)
            if st is None:
                continue
            merged_voxels.update(st.voxels)
            merged_provenance.update(st.provenance)
    state = BuildState(
        build_id="__merged__",
        origin=(0, 0, 0),
        voxels=merged_voxels,
        provenance=merged_provenance,
        script_path="",
        slot=0,
    )
    print(describe_context(pose, state))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(_cli())
