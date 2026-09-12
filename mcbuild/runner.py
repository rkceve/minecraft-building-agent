"""Send commands to the live server: ssh + the remote rcon_batch.py.

    python -m mcbuild.runner --file commands.txt
    python -m mcbuild.runner --deploy
    python -m mcbuild.runner --one "list"
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_TOML = Path(__file__).with_name("server.toml")
_LOCAL_BATCH_SCRIPT = Path(__file__).resolve().parent.parent / "rcon_batch.py"
_FAIL_RE = re.compile(r"^FAIL\t([^\t]*)\t(.*)$")
_SUMMARY_RE = re.compile(r"^(\d+) ok, (\d+) failed$")


@dataclass
class ServerConfig:
    """Loaded from mcbuild/server.toml."""

    ssh_host: str = "claude@minecraft-server"
    remote_dir: str = "~/buildagent-server"
    rcon_port: int = 25576
    password_file: str = "~/buildagent-server/.rcon-password"
    log_path: str = "~/buildagent-server/logs/latest.log"


@dataclass
class RunResult:
    ok: int
    failed: list[tuple[str, str]]
    seconds: float


def load_config(path: str | Path = _DEFAULT_TOML) -> ServerConfig:
    """Read a `ServerConfig` from a toml file."""
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return ServerConfig(**data)


def _unescape(text: str) -> str:
    """Inverse of rcon_batch.py's backslash escaping of response lines."""
    return text.replace("\\\\", "\\")


def _remote_batch_cmd(cfg: ServerConfig, rate: float = 0) -> str:
    return (
        f"python3 {cfg.remote_dir}/rcon_batch.py "
        f"--port {cfg.rcon_port} --password-file {cfg.password_file} --rate {rate}"
    )


def run_commands(cmds: list[str], cfg: ServerConfig, rate: float = 0) -> RunResult:
    """Pipe `cmds` to the remote rcon_batch.py over one ssh session.

    `rate` caps commands per second (0 = unlimited), so a build can be
    streamed visibly instead of landing all at once.
    """
    start = time.perf_counter()
    proc = subprocess.run(
        ["ssh", cfg.ssh_host, _remote_batch_cmd(cfg, rate)],
        input="\n".join(cmds) + "\n",
        capture_output=True,
        text=True,
    )
    seconds = time.perf_counter() - start
    ok = 0
    failed: list[tuple[str, str]] = []
    for line in proc.stderr.splitlines():
        m = _FAIL_RE.match(line)
        if m:
            failed.append((m.group(1), _unescape(m.group(2))))
            continue
        m = _SUMMARY_RE.match(line)
        if m:
            ok = int(m.group(1))
    return RunResult(ok=ok, failed=failed, seconds=seconds)


def deploy_batch_script(cfg: ServerConfig) -> None:
    """scp rcon_batch.py to the remote_dir (safe to re-run)."""
    subprocess.run(["ssh", cfg.ssh_host, f"mkdir -p {cfg.remote_dir}"], check=True)
    subprocess.run(
        ["scp", str(_LOCAL_BATCH_SCRIPT), f"{cfg.ssh_host}:{cfg.remote_dir}/rcon_batch.py"],
        check=True,
    )


def rcon_one(cmd: str, cfg: ServerConfig) -> str:
    """Run a single command over ssh and return the server's response text."""
    proc = subprocess.run(
        ["ssh", cfg.ssh_host, _remote_batch_cmd(cfg)],
        input=cmd + "\n",
        capture_output=True,
        text=True,
    )
    lines = proc.stdout.splitlines()
    return _unescape(lines[0]) if lines else ""


def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Send commands to the buildagent server.")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="command file to send, one command per line")
    group.add_argument("--deploy", action="store_true", help="deploy rcon_batch.py to the server")
    group.add_argument("--one", help="run a single command and print the response")
    ap.add_argument("--rate", type=float, default=0, help="max commands/sec for --file, 0 = unlimited")
    args = ap.parse_args(argv)
    cfg = load_config()

    if args.deploy:
        deploy_batch_script(cfg)
        print("deployed rcon_batch.py")
        return 0
    if args.one is not None:
        print(rcon_one(args.one, cfg))
        return 0
    cmds = [line.strip() for line in Path(args.file).read_text().splitlines() if line.strip()]
    result = run_commands(cmds, cfg, rate=args.rate)
    print(f"{result.ok} ok, {len(result.failed)} failed in {result.seconds:.1f}s")
    for cmd, response in result.failed:
        print(f"FAIL\t{cmd}\t{response}", file=sys.stderr)
    return 1 if result.failed else 0


if __name__ == "__main__":
    sys.exit(_cli())
