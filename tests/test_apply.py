import json

import pytest

from mcbuild import apply as applymod
from mcbuild.apply import ApplyResult, BuildState, apply_build, diff, load_state, save_state, slot_for, undo_build
from mcbuild.runner import RunResult


class FakeCfg:
    pass


class Recorder:
    """Fake runner.run_commands: records every command list it was given."""

    def __init__(self, failed_cmds=None):
        self.calls: list[list[str]] = []
        self.failed_cmds = set(failed_cmds or ())

    def __call__(self, cmds, cfg, rate=0):
        self.calls.append(list(cmds))
        failed = [(c, "fail") for c in cmds if c in self.failed_cmds]
        ok = len(cmds) - len(failed)
        return RunResult(ok=ok, failed=failed, seconds=0.01)


@pytest.fixture(autouse=True)
def _isolated_state_dir(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(applymod, "STATE_DIR", state_dir)
    yield state_dir


# --- diff -------------------------------------------------------------


def test_diff_added_and_removed():
    old = {(0, 0, 0): "stone", (1, 0, 0): "dirt"}
    new = {(0, 0, 0): "stone", (2, 0, 0): "sand"}
    changed, removed = diff(old, new)
    assert changed == {(2, 0, 0): "sand"}
    assert removed == {(1, 0, 0)}


def test_diff_block_state_changed():
    old = {(0, 0, 0): "oak_stairs[facing=north,half=top]"}
    new = {(0, 0, 0): "oak_stairs[facing=south,half=top]"}
    changed, removed = diff(old, new)
    assert changed == {(0, 0, 0): "oak_stairs[facing=south,half=top]"}
    assert removed == set()


def test_diff_no_change():
    old = {(0, 0, 0): "stone"}
    new = {(0, 0, 0): "stone"}
    changed, removed = diff(old, new)
    assert changed == {}
    assert removed == set()


# --- state round-trip ---------------------------------------------------


def test_state_round_trip(_isolated_state_dir):
    st = BuildState(
        build_id="chapel",
        origin=(10, 1, -3),
        voxels={(0, 0, 0): "stone", (1, 0, 0): "oak_stairs[facing=north,half=top]"},
        provenance={(0, 0, 0): "wall_0", (1, 0, 0): "wall_0"},
        script_path="build.py",
        slot=5,
    )
    save_state(st)
    loaded = load_state("chapel")
    assert loaded == st


def test_load_state_missing_returns_none(_isolated_state_dir):
    assert load_state("does_not_exist") is None


def test_slot_for_stable_and_in_range():
    s1 = slot_for("chapel")
    s2 = slot_for("chapel")
    assert s1 == s2
    assert 1 <= s1 <= 200
    assert slot_for("chapel") != slot_for("tower") or True  # not guaranteed unique, just in range


# --- apply_build --------------------------------------------------------


def _write_dump(tmp_path, voxels, provenance=None, elements=None):
    provenance = provenance or {}
    dump = {
        "voxels": [[x, y, z, b] for (x, y, z), b in voxels.items()],
        "provenance": [[x, y, z, e] for (x, y, z), e in provenance.items()],
        "elements": elements or {},
    }
    path = tmp_path / "out.json"
    path.write_text(json.dumps(dump))
    return str(path)


def test_first_apply_backs_up_and_places_all_voxels(tmp_path, monkeypatch):
    voxels = {(0, 0, 0): "stone", (1, 0, 0): "stone", (2, 0, 0): "dirt"}
    dump_path = _write_dump(tmp_path, voxels)

    recorder = Recorder()
    monkeypatch.setattr("mcbuild.runner.run_commands", recorder)

    result = apply_build("chapel", dump_path, FakeCfg())

    assert isinstance(result, ApplyResult)
    assert result.failed == []
    cmds = recorder.calls[0]
    assert any(c.startswith("clone ") for c in cmds), "expected a clone backup on first apply"
    # all three voxels should appear as setblock/fill commands
    joined = "\n".join(cmds)
    assert "stone" in joined
    assert "dirt" in joined
    assert result.added == 3
    assert result.removed == 0

    # state persisted
    st = load_state("chapel")
    assert st is not None
    assert st.voxels == voxels


def test_second_apply_emits_minimal_diff(tmp_path, monkeypatch):
    voxels_v1 = {(0, 0, 0): "stone", (1, 0, 0): "stone"}
    dump1 = _write_dump(tmp_path, voxels_v1)
    recorder = Recorder()
    monkeypatch.setattr("mcbuild.runner.run_commands", recorder)
    apply_build("chapel", dump1, FakeCfg())

    # move block (1,0,0) to (5,0,0)
    voxels_v2 = {(0, 0, 0): "stone", (5, 0, 0): "stone"}
    dump2 = _write_dump(tmp_path, voxels_v2)
    recorder.calls.clear()
    result = apply_build("chapel", dump2, FakeCfg())

    assert result.failed == []
    cmds = recorder.calls[0]
    assert not any(c.startswith("clone ") for c in cmds), "no backup expected on second apply"

    air_cmds = [c for c in cmds if c.endswith(" air")]
    placement_cmds = [c for c in cmds if "stone" in c]
    assert len(air_cmds) == 1
    assert len(placement_cmds) == 1
    assert "1 0 0" in air_cmds[0]
    assert "5 0 0" in placement_cmds[0]

    forceload_cmds = [c for c in cmds if c.startswith("forceload")]
    assert len(forceload_cmds) >= 2  # at least one add, one remove

    st = load_state("chapel")
    assert st.voxels == voxels_v2


def test_apply_failure_does_not_save_state(tmp_path, monkeypatch):
    voxels = {(0, 0, 0): "stone"}
    dump_path = _write_dump(tmp_path, voxels)
    recorder = Recorder(failed_cmds={"setblock 0 0 0 stone"})
    monkeypatch.setattr("mcbuild.runner.run_commands", recorder)

    result = apply_build("chapel", dump_path, FakeCfg())
    assert result.failed
    assert load_state("chapel") is None


def test_undo_restores_and_deletes_state(tmp_path, monkeypatch):
    voxels = {(0, 0, 0): "stone"}
    dump_path = _write_dump(tmp_path, voxels)
    recorder = Recorder()
    monkeypatch.setattr("mcbuild.runner.run_commands", recorder)
    apply_build("chapel", dump_path, FakeCfg())
    assert load_state("chapel") is not None

    recorder.calls.clear()
    result = undo_build("chapel", FakeCfg())
    assert result.failed == []
    cmds = recorder.calls[0]
    assert any(c.startswith("clone ") for c in cmds), "undo should clone the backup back"
    assert load_state("chapel") is None


def test_undo_after_growth_restores_original_box_and_clears_outside(tmp_path, monkeypatch):
    # first apply: small box backed up as backup_box
    voxels_v1 = {(0, 0, 0): "stone", (1, 0, 0): "stone"}
    dump1 = _write_dump(tmp_path, voxels_v1)
    recorder = Recorder()
    monkeypatch.setattr("mcbuild.runner.run_commands", recorder)
    apply_build("chapel", dump1, FakeCfg())

    st_after_v1 = load_state("chapel")
    assert st_after_v1.backup_box == (0, 0, 0, 1, 0, 0)

    # second apply: adds voxels far outside the original backup_box
    voxels_v2 = {(0, 0, 0): "stone", (1, 0, 0): "stone", (50, 0, 50): "dirt"}
    dump2 = _write_dump(tmp_path, voxels_v2)
    apply_build("chapel", dump2, FakeCfg())

    st_after_v2 = load_state("chapel")
    # backup_box is carried forward unchanged, not extended
    assert st_after_v2.backup_box == (0, 0, 0, 1, 0, 0)
    assert st_after_v2.voxels == voxels_v2

    recorder.calls.clear()
    result = undo_build("chapel", FakeCfg())
    assert result.failed == []
    cmds = recorder.calls[0]

    clone_cmds = [c for c in cmds if c.startswith("clone ")]
    assert clone_cmds, "expected the original backup_box to be restored via clone"

    air_cmds = [c for c in cmds if c.endswith(" air")]
    assert len(air_cmds) == 1
    assert "50 0 50" in air_cmds[0]

    forceload_cmds = [c for c in cmds if c.startswith("forceload")]
    assert len(forceload_cmds) >= 2

    assert load_state("chapel") is None


def test_undo_no_state_reports_failure(tmp_path, monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr("mcbuild.runner.run_commands", recorder)
    result = undo_build("nonexistent", FakeCfg())
    assert result.failed
    assert recorder.calls == []
