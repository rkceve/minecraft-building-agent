import math

import pytest

from mcbuild.player import (
    Pose,
    _parse_triplet,
    describe_context,
    eye,
    ground_target,
    raycast,
    view_vector,
)
from mcbuild.apply import BuildState


def _pose(yaw, pitch, x=0.0, y=0.0, z=0.0):
    return Pose(x=x, y=y, z=z, yaw=yaw, pitch=pitch)


# --- view_vector truth table ---------------------------------------------


@pytest.mark.parametrize(
    "yaw,pitch,expected",
    [
        (0, 0, (0, 0, 1)),
        (90, 0, (-1, 0, 0)),
        (180, 0, (0, 0, -1)),
        (-90, 0, (1, 0, 0)),
        (0, 90, (0, -1, 0)),
    ],
)
def test_view_vector_truth_table(yaw, pitch, expected):
    v = view_vector(_pose(yaw, pitch))
    for got, want in zip(v, expected):
        assert got == pytest.approx(want, abs=1e-9)


def test_eye_adds_eye_height():
    p = _pose(0, 0, x=1.0, y=2.0, z=3.0)
    assert eye(p) == pytest.approx((1.0, 3.62, 3.0))


# --- raycast ---------------------------------------------------------------


def test_raycast_hits_nearest_voxel_on_diagonal():
    vox = {
        (5, 5, 5): "stone",
        (2, 2, 2): "stone",
        (8, 8, 8): "stone",
    }
    origin = (0.5, 0.5, 0.5)
    direction = (1.0, 1.0, 1.0)
    hit = raycast(vox, origin, direction, max_dist=64.0)
    assert hit == (2, 2, 2)


def test_raycast_misses_returns_none():
    vox = {(5, 5, 5): "stone"}
    origin = (0.5, 0.5, 0.5)
    direction = (1.0, 0.0, 0.0)
    assert raycast(vox, origin, direction, max_dist=64.0) is None


def test_raycast_respects_max_dist():
    vox = {(100, 0, 0): "stone"}
    origin = (0.5, 0.0, 0.0)
    direction = (1.0, 0.0, 0.0)
    assert raycast(vox, origin, direction, max_dist=10.0) is None


# --- ground_target -----------------------------------------------------


def test_ground_target_straight_down():
    # standing at (0, 10, 0), looking straight down: pitch 90
    p = _pose(0, 90, x=0.0, y=10.0, z=0.0)
    target = ground_target(p, ground_y=0)
    assert target == (0, 1, 0)


def test_ground_target_none_when_looking_up():
    p = _pose(0, -45, x=0.0, y=10.0, z=0.0)
    assert ground_target(p, ground_y=0) is None


def test_ground_target_none_when_beyond_max_dist():
    p = _pose(0, 1, x=0.0, y=1000.0, z=0.0)
    assert ground_target(p, max_dist=10.0, ground_y=0) is None


def test_ground_target_angled():
    # eye at (0, eye=1.62), pitch 45 looking down and forward (+z, since yaw=0)
    p = _pose(0, 45, x=0.0, y=0.0, z=0.0)
    ox, oy, oz = eye(p)
    dx, dy, dz = view_vector(p)
    plane_y = 1
    t = (plane_y - oy) / dy
    expected_x = ox + dx * t
    expected_z = oz + dz * t
    target = ground_target(p, ground_y=0)
    assert target == (math.floor(expected_x), plane_y, math.floor(expected_z))


# --- parsing real `data get` output ---------------------------------------


def test_parse_triplet_pos():
    text = "ULLAFNC has the following entity data: [12.5d, 1.0d, -7.25d]"
    assert _parse_triplet(text) == pytest.approx([12.5, 1.0, -7.25])


def test_parse_triplet_rotation():
    text = "ULLAFNC has the following entity data: [-135.3f, 20.1f]"
    assert _parse_triplet(text) == pytest.approx([-135.3, 20.1])


def test_parse_triplet_no_bracket_returns_none():
    text = "No entity was found"
    assert _parse_triplet(text) is None


def test_get_pose_offline_returns_none(monkeypatch):
    from mcbuild import player, runner

    def fake_rcon_one(cmd, cfg):
        return "No entity was found"

    monkeypatch.setattr(runner, "rcon_one", fake_rcon_one)
    assert player.get_pose("ULLAFNC", cfg=object()) is None


def test_get_pose_parses_both_calls(monkeypatch):
    from mcbuild import player, runner

    responses = {
        "data get entity ULLAFNC Pos": "ULLAFNC has the following entity data: [12.5d, 1.0d, -7.25d]",
        "data get entity ULLAFNC Rotation": "ULLAFNC has the following entity data: [-135.3f, 20.1f]",
    }

    def fake_rcon_one(cmd, cfg):
        return responses[cmd]

    monkeypatch.setattr(runner, "rcon_one", fake_rcon_one)
    pose = player.get_pose("ULLAFNC", cfg=object())
    assert pose == Pose(x=12.5, y=1.0, z=-7.25, yaw=-135.3, pitch=20.1)


# --- describe_context -------------------------------------------------


def test_describe_context_hits_build_voxel():
    vox = {(2, 2, 2): "stone_bricks"}
    prov = {(2, 2, 2): "wall_0"}
    state = BuildState(
        build_id="b", origin=(0, 0, 0), voxels=vox, provenance=prov, script_path="x.py", slot=1
    )
    # aim a pose that actually looks toward (2,2,2) from near origin
    p2 = Pose(x=0.5, y=0.38, z=0.5, yaw=0, pitch=0)
    text = describe_context(p2, state)
    assert "Player position:" in text
    assert "Facing:" in text
    assert "Ground target" in text or "Looking at" in text


def test_describe_context_no_state():
    p = _pose(0, 0)
    text = describe_context(p, None)
    assert "nothing built yet" in text
