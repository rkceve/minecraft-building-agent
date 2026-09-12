import io
import socket
import struct
import threading
import time

import pytest

import rcon_batch

AUTH = 3
COMMAND = 2
RESPONSE = 0


def _packet(request_id: int, ptype: int, body: str) -> bytes:
    payload = body.encode()
    return struct.pack("<iii", 10 + len(payload), request_id, ptype) + payload + b"\x00\x00"


def _parse_first_packet(data: bytes) -> tuple[int, int, str]:
    """Parse only the first packet in `data`, ignoring any bytes after it."""
    (length,) = struct.unpack("<i", data[:4])
    body_bytes = data[4 : 4 + length]
    request_id, ptype = struct.unpack("<ii", body_bytes[:8])
    return request_id, ptype, body_bytes[8:-2].decode()


class QuirkyFakeRcon(threading.Thread):
    """Mimics Minecraft's RCON quirk: one recv(4096) per loop iteration, and
    only the first packet in that read is processed. A second packet sent
    back-to-back in the same TCP segment is silently dropped, never answered.
    """

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]

    def run(self) -> None:
        conn, _ = self.sock.accept()
        with conn:
            data = conn.recv(4096)
            if not data:
                return
            req_id, _ptype, _body = _parse_first_packet(data)
            conn.sendall(_packet(req_id, RESPONSE, ""))
            conn.sendall(_packet(req_id, AUTH, ""))
            while True:
                data = conn.recv(4096)
                if not data:
                    return
                req_id, _ptype, body = _parse_first_packet(data)
                reply = "That position is not loaded" if "bad" in body else ""
                conn.sendall(_packet(req_id, RESPONSE, reply))


def test_rcon_command_survives_single_packet_reads():
    """The current one-packet-per-command design works against the quirk."""
    server = QuirkyFakeRcon()
    server.start()
    rcon = rcon_batch.Rcon("127.0.0.1", server.port, "testpass")
    try:
        assert rcon.command("say hello") == ""
        assert rcon.command("bad teleport") == "That position is not loaded"
    finally:
        rcon.close()


def test_old_sentinel_design_fails_against_quirky_server():
    """The old design (command packet + empty sentinel back-to-back) breaks:
    the quirky server reads once, answers only the command packet, and the
    sentinel reply never arrives.
    """
    server = QuirkyFakeRcon()
    server.start()
    sock = socket.create_connection(("127.0.0.1", server.port), timeout=2)
    sock.sendall(_packet(1, AUTH, "testpass"))
    rcon_batch.read_packet(sock)  # empty response
    rcon_batch.read_packet(sock)  # auth ack

    # Old design: send the command and an empty "sentinel" command in one
    # write, so they land in the same TCP segment / recv() call.
    combined = _packet(2, COMMAND, "say hello") + _packet(3, COMMAND, "")
    sock.sendall(combined)
    got_id, _ptype, body = rcon_batch.read_packet(sock)
    assert got_id == 2
    assert body == ""

    sock.settimeout(0.3)
    with pytest.raises((TimeoutError, EOFError)):
        rcon_batch.read_packet(sock)  # sentinel (id 3) never arrives
    sock.close()


def test_rcon_batch_reports_failures(tmp_path, monkeypatch, capsys):
    server = QuirkyFakeRcon()
    server.start()

    password_file = tmp_path / ".rcon-password"
    password_file.write_text("testpass")

    stdin = io.StringIO("fill 0 0 0 1 1 1 stone\nsay hello\nbad teleport\n")
    monkeypatch.setattr("sys.stdin", stdin)

    argv = ["--host", "127.0.0.1", "--port", str(server.port), "--password-file", str(password_file)]
    code = rcon_batch.main(argv)

    captured = capsys.readouterr()
    assert code == 1
    assert "2 ok, 1 failed" in captured.err
    assert "bad teleport" in captured.err


def test_rate_limits_commands_per_second(tmp_path, monkeypatch):
    server = QuirkyFakeRcon()
    server.start()

    password_file = tmp_path / ".rcon-password"
    password_file.write_text("testpass")

    stdin = io.StringIO("say one\nsay two\nsay three\n")
    monkeypatch.setattr("sys.stdin", stdin)

    argv = [
        "--host", "127.0.0.1",
        "--port", str(server.port),
        "--password-file", str(password_file),
        "--rate", "2",
    ]
    start = time.perf_counter()
    code = rcon_batch.main(argv)
    elapsed = time.perf_counter() - start

    assert code == 0
    assert elapsed >= 1.0


def test_is_failure_markers():
    assert rcon_batch.is_failure("That position is not loaded")
    assert rcon_batch.is_failure("Unknown command")
    assert not rcon_batch.is_failure("")
