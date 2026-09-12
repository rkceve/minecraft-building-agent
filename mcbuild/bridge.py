"""Chat -> codex -> preview -> apply loop.

    python -m mcbuild.bridge --config mcbuild/server.toml [--workdir builds]
        [--build-id church] [--dry-run] [--log-stdin] [--rate 20]

Tails the server log over ssh, watches for player chat commands
(`!build`, `!fix`/`!modify`, `!undo`, `!cancel`, `!status`), and for
`!build`/`!fix` drives one codex turn: compose a prompt, run codex
non-interactively against `builds/<build_id>/build.py`, then preview and
apply the result, reporting back to players via tellraw.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from mcbuild.runner import ServerConfig, load_config, rcon_one

_CHAT_RE = re.compile(r"<(\w+)>\s+(!\w+)(.*)$")

_ALIASES = {
    "build": "build",
    "fix": "fix",
    "modify": "fix",
    "undo": "undo",
    "cancel": "cancel",
    "status": "status",
}

_DEFAULT_CODEX_BIN = (
    r"%LOCALAPPDATA%\OpenAI\Codex\bin\7ac07f4ce733f89a\codex.exe"
)

_PROMPT_PATH = Path(__file__).with_name("prompts") / "turn_prefix.txt"
_TEMPLATE_PATH = Path(__file__).with_name("templates") / "build_template.py"
_AGENTS_MD_PATH = Path(__file__).with_name("prompts") / "AGENTS.md"


@dataclass
class ChatCommand:
    player: str
    command: str  # normalized: build, fix, undo, cancel, status
    text: str


def parse_chat_line(line: str) -> ChatCommand | None:
    """Extract a `!command` chat message from one server log line.

    Tolerates Paper's `[HH:MM:SS INFO]:` prefix, the `[Not Secure]` prefix,
    and anything else before `<player>`. Returns None for lines that don't
    contain a recognized `!command`.
    """
    m = _CHAT_RE.search(line)
    if not m:
        return None
    player, raw_command, text = m.group(1), m.group(2), m.group(3)
    name = raw_command[1:].lower()
    command = _ALIASES.get(name)
    if command is None:
        return None
    return ChatCommand(player=player, command=command, text=text.strip())


def _resolve_codex_bin() -> str:
    env = os.environ.get("CODEX_BIN")
    if env:
        return env
    default = os.path.expandvars(_DEFAULT_CODEX_BIN)
    if Path(default).exists():
        return default
    return "codex"


def _gather_context(player: str, cfg: ServerConfig, state: dict) -> str:
    """Best-effort player context via mcbuild.player (owned by another agent).

    Imported lazily so bridge.py stays importable / testable before that
    module exists. Any failure (missing module, missing function, exception,
    or a None result) degrades to an empty string rather than failing the
    turn.
    """
    try:
        from mcbuild import player as player_mod  # noqa: PLC0415

        pose = player_mod.get_pose(player, cfg)
        context = player_mod.describe_context(pose, state)
    except Exception:
        return ""
    return context or ""


def compose_prompt(
    command: str,
    player: str,
    text: str,
    context: str,
    build_id: str,
    script_path: str,
    prompt_path: Path = _PROMPT_PATH,
) -> str:
    template = prompt_path.read_text(encoding="utf-8")
    return template.format(
        command=command,
        player=player,
        text=text,
        context=context,
        build_id=build_id,
        script_path=script_path,
    )


def _tellraw_json(text: str, color: str) -> str:
    return json.dumps([{"text": text, "color": color}])


def _codex_command(codex_bin: str, workdir: Path) -> list[str]:
    return [
        codex_bin,
        "exec",
        "-m",
        "gpt-6-astra",
        "--skip-git-repo-check",
        "-s",
        "workspace-write",
        "-C",
        str(workdir),
        "-c",
        "model_reasoning_effort=medium",
        "--json",
        "-",
    ]


def extract_final_message(stdout: str) -> str | None:
    """Pull the last agent_message text out of a codex `--json` JSONL stream."""
    final: str | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                final = item["text"]
    return final


def _format_apply_summary(stdout: str, seconds: float) -> str:
    """Best-effort "+N -M blocks, T s" summary from mcbuild.apply's stdout.

    mcbuild.apply's exact stdout contract belongs to another agent; this
    tries a few plausible key names and otherwise falls back to relaying
    the raw output so a turn never silently loses its summary.
    """
    added = removed = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        kv = re.match(r"added=(\d+) removed=(\d+) commands=\d+ ok=\d+ failed=(\d+) in ([\d.]+)s", line)
        if kv:
            added, removed, nfail, secs = kv.groups()
            tail = f", {nfail} failed" if nfail != "0" else ""
            return f"+{added} -{removed} blocks, {float(secs):.1f}s{tail}"
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for key in ("added", "placed", "ok"):
            if key in data:
                added = data[key]
                break
        for key in ("removed", "cleared", "failed"):
            if key in data:
                removed = data[key]
                break
        if "seconds" in data:
            seconds = data["seconds"]
        break
    if added is not None and removed is not None:
        return f"+{added} -{removed} blocks, {seconds:.1f}s"
    trimmed = stdout.strip().splitlines()
    tail = trimmed[-1] if trimmed else ""
    return f"applied ({seconds:.1f}s): {tail[:150]}" if tail else f"applied ({seconds:.1f}s)"


class Bridge:
    def __init__(
        self,
        cfg: ServerConfig,
        workdir_base: Path,
        build_id: str,
        dry_run: bool,
        codex_bin: str,
        rate: float,
        log_path: Path,
    ) -> None:
        self.cfg = cfg
        self.build_id = build_id
        self.workdir = (workdir_base / build_id).resolve()
        self.dry_run = dry_run
        self.codex_bin = codex_bin
        self.rate = rate
        self.turn_n = 0
        self.turn_lock = threading.Lock()
        self.proc: subprocess.Popen | None = None
        self.proc_lock = threading.Lock()
        self.turn_queue: queue.Queue[ChatCommand] = queue.Queue()
        self.busy = threading.Event()
        self._log_lock = threading.Lock()
        self.log_path = log_path
        self.dry_run_output: list[str] = []

    # -- logging -----------------------------------------------------
    def log(self, msg: str) -> None:
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        with self._log_lock:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    # -- tellraw -------------------------------------------------------
    def tellraw(self, text: str, color: str) -> None:
        payload = _tellraw_json(text, color)
        cmd = f"tellraw @a {payload}"
        if self.dry_run:
            self.dry_run_output.append(cmd)
            print(cmd)
            return
        rcon_one(cmd, self.cfg)

    # -- workdir setup ---------------------------------------------------
    def _ensure_workdir(self) -> Path:
        self.workdir.mkdir(parents=True, exist_ok=True)
        (self.workdir / "logs").mkdir(parents=True, exist_ok=True)
        script_path = self.workdir / "build.py"
        if not script_path.exists():
            if self.dry_run:
                self.dry_run_output.append(f"copy {_TEMPLATE_PATH} -> {script_path}")
            else:
                shutil.copyfile(_TEMPLATE_PATH, script_path)
        for name in ("AGENTS.md", "DSL_REFERENCE.md"):
            src = _AGENTS_MD_PATH.with_name(name)
            if src.exists():
                dest = self.workdir / name
                if self.dry_run:
                    self.dry_run_output.append(f"copy {src} -> {dest}")
                else:
                    shutil.copyfile(src, dest)
        return script_path

    # -- one turn ------------------------------------------------------
    def run_turn(self, cmd: ChatCommand) -> None:
        script_path = self._ensure_workdir()
        context = _gather_context(cmd.player, self.cfg, {"build_id": self.build_id})
        prompt = compose_prompt(
            command=cmd.command,
            player=cmd.player,
            text=cmd.text,
            context=context,
            build_id=self.build_id,
            script_path=str(script_path),
        )
        with self.turn_lock:
            self.turn_n += 1
            turn_n = self.turn_n
        codex_argv = _codex_command(self.codex_bin, self.workdir)
        self.log(f"turn {turn_n} player={cmd.player} command={cmd.command}")

        if self.dry_run:
            self.dry_run_output.append("PROMPT:\n" + prompt)
            self.dry_run_output.append("CODEX CMD: " + " ".join(codex_argv))
            print("PROMPT:\n" + prompt)
            print("CODEX CMD: " + " ".join(codex_argv))
            return

        self.busy.set()
        try:
            with self.proc_lock:
                self.proc = subprocess.Popen(
                    codex_argv,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=str(self.workdir),
                )
            proc = self.proc
            assert proc is not None
            stdout, stderr = proc.communicate(input=prompt)
            returncode = proc.returncode
            with self.proc_lock:
                self.proc = None

            log_file = self.workdir / "logs" / f"turn_{turn_n}.jsonl"
            stdout = stdout or ""
            stderr = stderr or ""
            log_file.write_text(stdout, encoding="utf-8")

            if returncode != 0:
                self.log(f"turn {turn_n} codex failed rc={returncode} stderr={stderr[:500]}")
                self.tellraw(f"codex failed: {stderr.strip()[:200]}", "red")
                return

            final_message = extract_final_message(stdout)
            self.log(f"turn {turn_n} codex ok final={final_message!r}")

            self._run_preview_and_apply(turn_n)
        finally:
            self.busy.clear()

    def _run_preview_and_apply(self, turn_n: int) -> None:
        out_json = self.workdir / "out.json"
        script_path = self.workdir / "build.py"
        preview_argv = [
            sys.executable,
            "-m",
            "mcbuild.preview",
            str(script_path),
            "--json",
            str(out_json),
        ]
        preview = subprocess.run(preview_argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if preview.returncode != 0:
            err = (preview.stderr or preview.stdout).strip()
            self.log(f"turn {turn_n} preview failed: {err[:500]}")
            self.tellraw(f"preview failed: {err[:200]}", "red")
            return

        apply_argv = [
            sys.executable,
            "-m",
            "mcbuild.apply",
            "--id",
            self.build_id,
            "--json",
            str(out_json),
            "--rate",
            str(self.rate),
        ]
        start = time.perf_counter()
        apply_run = subprocess.run(apply_argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
        seconds = time.perf_counter() - start
        if apply_run.returncode != 0:
            err = (apply_run.stderr or apply_run.stdout).strip()
            self.log(f"turn {turn_n} apply failed: {err[:500]}")
            self.tellraw(f"apply failed: {err[:200]}", "red")
            return

        summary = _format_apply_summary(apply_run.stdout, seconds)
        self.log(f"turn {turn_n} applied: {summary}")
        self.tellraw(summary, "gold")

    # -- undo / cancel / status ------------------------------------------
    def run_undo(self, cmd: ChatCommand) -> None:
        self.log(f"undo requested by {cmd.player}")
        if self.dry_run:
            argv = [
                sys.executable,
                "-m",
                "mcbuild.apply",
                "--id",
                self.build_id,
                "--undo",
            ]
            self.dry_run_output.append("UNDO CMD: " + " ".join(argv))
            print("UNDO CMD: " + " ".join(argv))
            return
        argv = [sys.executable, "-m", "mcbuild.apply", "--id", self.build_id, "--undo"]
        result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            err = (result.stderr or result.stdout).strip()
            self.log(f"undo failed: {err[:500]}")
            self.tellraw(f"undo failed: {err[:200]}", "red")
        else:
            self.log("undo ok")
            self.tellraw("undo complete", "gold")

    def handle_cancel(self, cmd: ChatCommand) -> None:
        self.log(f"cancel requested by {cmd.player}")
        with self.proc_lock:
            proc = self.proc
            if proc is not None and proc.poll() is None:
                proc.kill()
                self.tellraw("build cancelled", "gray")
                return
        self.tellraw("nothing to cancel", "gray")

    def handle_status(self, cmd: ChatCommand) -> None:
        running = self.busy.is_set()
        msg = "a turn is running" if running else "idle"
        self.tellraw(f"status: {msg}", "gray")

    # -- dispatch / main loop --------------------------------------------
    def dispatch(self, cmd: ChatCommand) -> None:
        if cmd.command in ("build", "fix"):
            self.turn_queue.put(cmd)
        elif cmd.command == "undo":
            self.turn_queue.put(cmd)
        elif cmd.command == "cancel":
            self.handle_cancel(cmd)
        elif cmd.command == "status":
            self.handle_status(cmd)

    def worker(self) -> None:
        while True:
            cmd = self.turn_queue.get()
            try:
                if cmd.command in ("build", "fix"):
                    self.run_turn(cmd)
                elif cmd.command == "undo":
                    self.run_undo(cmd)
            finally:
                self.turn_queue.task_done()

    def feed_lines(self, lines: "list[str] | object") -> None:
        for raw_line in lines:
            cmd = parse_chat_line(raw_line)
            if cmd is not None:
                self.dispatch(cmd)

    def run(self, lines: "list[str] | object") -> None:
        worker_thread = threading.Thread(target=self.worker, daemon=True)
        worker_thread.start()
        self.feed_lines(lines)
        self.turn_queue.join()


def _tail_ssh(cfg: ServerConfig):
    proc = subprocess.Popen(
        ["ssh", cfg.ssh_host, "tail", "-n", "0", "-F", cfg.log_path],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        yield line


def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Chat -> codex -> preview -> apply bridge.")
    ap.add_argument("--config", default=None, help="path to server.toml")
    ap.add_argument("--workdir", default="builds", help="base directory for per-build workdirs")
    ap.add_argument("--build-id", default="church", help="build id, selects builds/<id>/")
    ap.add_argument("--dry-run", action="store_true", help="print instead of executing")
    ap.add_argument("--log-stdin", action="store_true", help="read log lines from stdin")
    ap.add_argument("--rate", type=float, default=0, help="apply block placement rate")
    ap.add_argument("--bridge-log", default="bridge.log", help="path for the bridge's own log")
    args = ap.parse_args(argv)

    cfg = load_config(args.config) if args.config else load_config()
    codex_bin = _resolve_codex_bin()
    bridge = Bridge(
        cfg=cfg,
        workdir_base=Path(args.workdir),
        build_id=args.build_id,
        dry_run=args.dry_run,
        codex_bin=codex_bin,
        rate=args.rate,
        log_path=Path(args.bridge_log),
    )

    if args.log_stdin:
        bridge.run(sys.stdin)
    else:
        bridge.run(_tail_ssh(cfg))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
