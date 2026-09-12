import json
from pathlib import Path

from mcbuild import bridge

FIXTURE_DIR = Path(__file__).with_name("fixtures")


# -- log line parsing --------------------------------------------------


def test_parse_build_command():
    line = "[12:34:56 INFO]: <ULLAFNC> !build a small chapel"
    cmd = bridge.parse_chat_line(line)
    assert cmd is not None
    assert cmd.player == "ULLAFNC"
    assert cmd.command == "build"
    assert cmd.text == "a small chapel"


def test_parse_not_secure_prefix_undo():
    line = "[12:34:56 INFO]: [Not Secure] <ULLAFNC> !undo"
    cmd = bridge.parse_chat_line(line)
    assert cmd is not None
    assert cmd.player == "ULLAFNC"
    assert cmd.command == "undo"
    assert cmd.text == ""


def test_parse_modify_alias():
    line = "[12:34:56 INFO]: <ULLAFNC> !modify add a tower"
    cmd = bridge.parse_chat_line(line)
    assert cmd is not None
    assert cmd.command == "fix"
    assert cmd.text == "add a tower"


def test_parse_cancel_status():
    assert bridge.parse_chat_line("[12:34:56 INFO]: <A> !cancel").command == "cancel"
    assert bridge.parse_chat_line("[12:34:56 INFO]: <A> !status").command == "status"


def test_parse_server_message_does_not_match():
    line = "[12:34:56 INFO]: ULLAFNC left the game"
    assert bridge.parse_chat_line(line) is None


def test_parse_plain_chat_does_not_match():
    line = "[12:34:56 INFO]: <ULLAFNC> hello there"
    assert bridge.parse_chat_line(line) is None


def test_parse_unknown_command_ignored():
    line = "[12:34:56 INFO]: <ULLAFNC> !dance"
    assert bridge.parse_chat_line(line) is None


# -- prompt composition --------------------------------------------------


def test_compose_prompt_fills_all_variables(tmp_path):
    template = tmp_path / "turn_prefix.txt"
    template.write_text(
        "cmd={command} player={player} text={text} ctx={context} "
        "id={build_id} script={script_path}",
        encoding="utf-8",
    )
    prompt = bridge.compose_prompt(
        command="build",
        player="ULLAFNC",
        text="a small chapel",
        context="standing near the plaza",
        build_id="church",
        script_path="/workdir/build.py",
        prompt_path=template,
    )
    assert prompt == (
        "cmd=build player=ULLAFNC text=a small chapel "
        "ctx=standing near the plaza id=church script=/workdir/build.py"
    )


def test_real_turn_prefix_template_is_formattable():
    # The shipped template must itself be a valid .format() target with the
    # documented variable names, and any other braces must be escaped.
    prompt = bridge.compose_prompt(
        command="build",
        player="ULLAFNC",
        text="a small chapel",
        context="",
        build_id="church",
        script_path="/workdir/build.py",
    )
    assert "ULLAFNC" in prompt
    assert "a small chapel" in prompt


# -- codex JSONL parsing --------------------------------------------------


def test_extract_final_message_from_recorded_sample():
    stdout = (FIXTURE_DIR / "codex_json_sample.jsonl").read_text(encoding="utf-8")
    assert bridge.extract_final_message(stdout) == "bridge ok"


def test_extract_final_message_takes_last_agent_message():
    stdout = "\n".join(
        [
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "first"}}),
            json.dumps({"type": "item.completed", "item": {"type": "reasoning", "text": "thinking"}}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "final one"}}),
        ]
    )
    assert bridge.extract_final_message(stdout) == "final one"


def test_extract_final_message_tolerates_malformed_lines():
    stdout = "not json\n" + json.dumps(
        {"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}
    )
    assert bridge.extract_final_message(stdout) == "ok"


def test_extract_final_message_none_when_absent():
    stdout = json.dumps({"type": "turn.started"})
    assert bridge.extract_final_message(stdout) is None


# -- dry-run end-to-end via --log-stdin -----------------------------------


def test_dry_run_end_to_end_build(tmp_path, monkeypatch, capsys):
    cfg = bridge.ServerConfig(
        ssh_host="claude@minecraft-server",
        remote_dir="~/buildagent-server",
        rcon_port=25576,
        password_file="~/buildagent-server/.rcon-password",
        log_path="~/buildagent-server/logs/latest.log",
    )

    # Any real subprocess call in dry-run mode is a bug: fail loudly.
    def _boom(*args, **kwargs):
        raise AssertionError("subprocess must not be invoked in --dry-run")

    monkeypatch.setattr(bridge.subprocess, "Popen", _boom)
    monkeypatch.setattr(bridge.subprocess, "run", _boom)
    monkeypatch.setattr(bridge, "rcon_one", _boom)

    workdir_base = tmp_path / "builds"
    br = bridge.Bridge(
        cfg=cfg,
        workdir_base=workdir_base,
        build_id="church",
        dry_run=True,
        codex_bin="codex",
        rate=0,
        log_path=tmp_path / "bridge.log",
    )

    lines = [
        "[12:34:56 INFO]: <ULLAFNC> !build a small chapel",
        "[12:34:57 INFO]: <ULLAFNC> hello there",  # ignored
    ]
    br.run(lines)

    out = "\n".join(br.dry_run_output)
    assert "PROMPT:" in out
    assert "a small chapel" in out
    assert "CODEX CMD:" in out
    assert "gpt-6-astra" in out
    assert "--json" in out
    assert (workdir_base / "church" / "build.py").exists() is False  # dry-run: not actually copied
    assert (tmp_path / "bridge.log").exists()


def test_dry_run_undo(tmp_path, monkeypatch):
    cfg = bridge.ServerConfig()

    def _boom(*args, **kwargs):
        raise AssertionError("subprocess must not be invoked in --dry-run")

    monkeypatch.setattr(bridge.subprocess, "run", _boom)
    monkeypatch.setattr(bridge, "rcon_one", _boom)

    br = bridge.Bridge(
        cfg=cfg,
        workdir_base=tmp_path / "builds",
        build_id="church",
        dry_run=True,
        codex_bin="codex",
        rate=0,
        log_path=tmp_path / "bridge.log",
    )
    br.run(["[12:34:56 INFO]: <ULLAFNC> !undo"])
    out = "\n".join(br.dry_run_output)
    assert "UNDO CMD:" in out
    assert "--undo" in out


def test_codex_command_uses_stdin_and_expected_flags(tmp_path):
    argv = bridge._codex_command("codex.exe", tmp_path)
    assert argv[0] == "codex.exe"
    assert argv[1] == "exec"
    assert "-m" in argv and "gpt-6-astra" in argv
    assert "--skip-git-repo-check" in argv
    assert "-s" in argv and "workspace-write" in argv
    assert "-C" in argv and str(tmp_path) in argv
    assert "--json" in argv
    assert argv[-1] == "-"  # prompt is piped on stdin, not passed as an arg
