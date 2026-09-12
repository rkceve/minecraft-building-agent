"""Send a batch of Minecraft commands over Source RCON, one per stdin line.

Runs on the server box with a bare python3; stdlib only.

    python3 rcon_batch.py --port 25576 --password-file ~/x/.rcon-password \
        [--progress-every 200] [--rate 40] < commands.txt

stdout: one line per input command holding that command's response, with
backslashes and newlines escaped. stderr: each failed command and the
`N ok, M failed` summary. Exit status is 1 if any command failed.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import struct
import sys
import time

AUTH = 3
COMMAND = 2
RESPONSE = 0
FAILURE_MARKERS = ("Unknown", "Incorrect", "not loaded", "Expected", "too many", "Cannot")


def packet(request_id: int, ptype: int, body: str) -> bytes:
    payload = body.encode()
    return struct.pack("<iii", 10 + len(payload), request_id, ptype) + payload + b"\x00\x00"


def read_packet(sock: socket.socket) -> tuple[int, int, str]:
    header = _recv_exactly(sock, 4)
    (length,) = struct.unpack("<i", header)
    if length < 10 or length > 4 * 1024 * 1024:
        raise ValueError(f"implausible packet length {length}")
    data = _recv_exactly(sock, length)
    request_id, ptype = struct.unpack("<ii", data[:8])
    return request_id, ptype, data[8:-2].decode(errors="replace")


def _recv_exactly(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("peer closed mid-packet")
        buf += chunk
    return buf


class RconError(Exception):
    """Authentication or framing failure."""


class Rcon:
    """A connected, authenticated RCON session."""

    def __init__(self, host: str, port: int, password: str, timeout: float = 30.0) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self._id = 0
        self._authenticate(password)

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _authenticate(self, password: str) -> None:
        request_id = self._next_id()
        self.sock.sendall(packet(request_id, AUTH, password))
        for _ in range(4):
            got_id, ptype, _body = read_packet(self.sock)
            if ptype == RESPONSE:
                continue
            if got_id == -1:
                raise RconError("RCON refused the password")
            return
        raise RconError("RCON never answered the password")

    def command(self, cmd: str) -> str:
        """Send one command and return its single response body.

        Minecraft's RCON (unlike Source's) answers with exactly one packet
        per command, truncated around 4096 bytes; it also processes only one
        packet per socket read, so a second packet sent back-to-back in the
        same TCP segment (the old "empty sentinel command" trick) gets
        silently dropped. Send one packet and read until the id matches.
        """
        request_id = self._next_id()
        self.sock.sendall(packet(request_id, COMMAND, cmd))
        while True:
            try:
                got_id, _ptype, body = read_packet(self.sock)
            except TimeoutError as exc:
                raise RconError(f"no response to {cmd!r} within {self.sock.gettimeout()}s") from exc
            if got_id == request_id:
                return body

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


def is_failure(response: str) -> bool:
    """A response is a failure if it carries one of the known server error markers."""
    return any(marker in response for marker in FAILURE_MARKERS)


def progress_command(done: int, total: int) -> str:
    text = f"[build] {done}/{total}"
    return "tellraw @a " + json.dumps({"text": text, "color": "gray"}, separators=(",", ":"))


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\n", "\n").replace("\r", "\r")


def unescape(text: str) -> str:
    """Inverse of the stdout escaping applied to each response line."""
    out = []
    it = iter(range(len(text)))
    chars = list(text)
    for i in it:
        if chars[i] == "\\" and i + 1 < len(chars):
            nxt = chars[i + 1]
            out.append({"n": "\n", "r": "\r", "\\": "\\"}.get(nxt, nxt))
            next(it, None)
        else:
            out.append(chars[i])
    return "".join(out)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run Minecraft commands from stdin over RCON.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--password-file", required=True)
    ap.add_argument("--progress-every", type=int, default=0)
    ap.add_argument("--rate", type=float, default=0, help="max commands/sec, 0 = unlimited")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    with open(os.path.expanduser(args.password_file)) as fh:
        password = fh.read().strip()
    commands = [line.strip() for line in sys.stdin.read().splitlines()]
    commands = [c for c in commands if c and not c.startswith("#")]

    try:
        rcon = Rcon(args.host, args.port, password)
    except (OSError, RconError, EOFError, ValueError) as exc:
        print(f"rcon connect failed: {exc}", file=sys.stderr)
        return 2

    ok = 0
    failed: list[tuple[str, str]] = []
    total = len(commands)
    try:
        for i, cmd in enumerate(commands, start=1):
            try:
                response = rcon.command(cmd)
            except (OSError, EOFError, ValueError) as exc:
                response = f"Cannot reach server: {exc}"
            sys.stdout.write(_escape(response) + "\n")
            if is_failure(response):
                failed.append((cmd, response))
                print(f"FAIL\t{cmd}\t{_escape(response)}", file=sys.stderr)
            else:
                ok += 1
            if args.progress_every > 0 and i % args.progress_every == 0 and i != total:
                try:
                    rcon.command(progress_command(i, total))
                except (OSError, EOFError, ValueError):
                    pass
            if args.rate > 0 and i != total:
                time.sleep(1.0 / args.rate)
    finally:
        rcon.close()
        sys.stdout.flush()
    print(f"{ok} ok, {len(failed)} failed", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
