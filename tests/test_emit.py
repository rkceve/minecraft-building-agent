import json
import re

from mcbuild import emit


def _parse_commands(cmds: list[str]) -> dict[tuple[int, int, int], str]:
    """Reverse of emit.to_commands: fill/setblock lines -> voxel dict."""
    out: dict[tuple[int, int, int], str] = {}
    for cmd in cmds:
        if cmd.startswith("setblock "):
            _, x, y, z, block = cmd.split(" ", 4)
            out[(int(x), int(y), int(z))] = block
        elif cmd.startswith("fill "):
            _, x0, y, z, x1, y2, z2, block = cmd.split(" ", 7)
            assert y == y2
            assert z == z2
            for x in range(int(x0), int(x1) + 1):
                out[(x, int(y), int(z))] = block
        else:
            raise AssertionError(f"unexpected command: {cmd}")
    return out


def _sample_voxels() -> dict[tuple[int, int, int], str]:
    vox: dict[tuple[int, int, int], str] = {}
    for x in range(5):
        vox[(x, 0, 0)] = "stone_bricks"
    vox[(2, 0, 0)] = "oak_stairs[facing=north,half=top]"
    vox[(10, 1, -3)] = "glass"
    vox[(0, 2, 5)] = "lantern"
    return vox


def test_round_trip():
    vox = _sample_voxels()
    cmds = emit.to_commands(vox)
    assert _parse_commands(cmds) == vox


def test_ordering_ascending_y_then_z_then_x():
    vox = {
        (5, 1, 0): "stone",
        (0, 0, 5): "stone",
        (0, 0, 0): "stone",
        (0, 1, 0): "stone",
    }
    cmds = emit.to_commands(vox)

    def key(cmd: str) -> tuple[int, int, int]:
        parts = cmd.split(" ")
        if parts[0] == "setblock":
            x, y, z = int(parts[1]), int(parts[2]), int(parts[3])
        else:
            x, y, z = int(parts[1]), int(parts[2]), int(parts[3])
        return (y, z, x)

    keys = [key(c) for c in cmds]
    assert keys == sorted(keys)


def test_forceload_chunk_math_negative_coords():
    assert -1 // 16 == -1
    box = (-20, 0, -20, 10, 5, 10)
    cmds = emit.forceload_commands(box, add=True)
    assert all(c.startswith("forceload add ") for c in cmds)
    coords = [tuple(int(p) for p in c.split(" ")[2:]) for c in cmds]
    xs = [x for c in coords for x in (c[0], c[2])]
    zs = [z for c in coords for z in (c[1], c[3])]
    assert min(xs) <= -32
    assert min(zs) <= -32


def test_backup_restore_tiling_large_box():
    box = (0, 0, 0, 63, 40, 63)  # 64 x 41 x 64, exceeds 32x32x32 per tile
    backup = emit.backup_commands(box, slot=1)
    restore = emit.restore_commands(box, slot=1)
    assert len(backup) == len(restore)

    covered: set[tuple[int, int, int]] = set()
    for cmd in backup:
        parts = cmd.split(" ")
        x0, y0, z0, x1, y1, z1 = (int(p) for p in parts[1:7])
        size = (x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1)
        assert size <= 32768
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    covered.add((x, y, z))

    x0, y0, z0, x1, y1, z1 = box
    expected = {
        (x, y, z)
        for x in range(x0, x1 + 1)
        for y in range(y0, y1 + 1)
        for z in range(z0, z1 + 1)
    }
    assert covered == expected


def test_say_json_escaping():
    cmd = emit.say('He said "hi\\there"')
    prefix = "tellraw @a "
    assert cmd.startswith(prefix)
    payload = json.loads(cmd[len(prefix):])
    assert payload["text"] == 'He said "hi\\there"'
    assert payload["color"] == "gold"
    # the emitted JSON itself must carry escaped quotes and backslashes
    raw = cmd[len(prefix):]
    assert re.search(r'\\"', raw)
    assert re.search(r"\\\\", raw)
