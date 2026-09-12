# mcbuild — module contracts (fixed; do not invent other interfaces)

Package: `mcbuild/` (Python 3.12, stdlib + numpy + nbtlib + mcp). Run modules as `python -m mcbuild.<module>`.
Tests: `tests/` with pytest. Keep each module importable without a Minecraft server.

## Shared data type
```python
Voxels = dict[tuple[int, int, int], str]   # (x, y, z) world coords -> "block_name[prop=val,...]"
```
Block names have no `minecraft:` prefix. Air is never stored. Property order inside `[...]` is arbitrary.

## Layer 1: reference → motifs (owner: Fable)
- `mcbuild/litematic.py`: `load_voxels(path) -> Voxels` (done)
- `mcbuild/ascii.py`: `elevation(vox, face, bounds=None) -> str` (done)
- `mcbuild/rotate.py`, `mcbuild/motifs.py`, `mcbuild/massing.py`, `mcbuild/style.py`:
  `style.apply(spec: dict, catalog) -> Voxels` (world coords, already offset by `spec["origin"]`).

## Layer 2: realization (owner: implementation agent A)
### `mcbuild/emit.py`
```python
def bounds(vox: Voxels) -> tuple[int,int,int,int,int,int]      # x0,y0,z0,x1,y1,z1 inclusive
def to_commands(vox: Voxels) -> list[str]
```
- Output: Minecraft console commands WITHOUT leading slash, e.g. `fill 10 0 5 14 0 5 stone_bricks` and `setblock 3 4 5 oak_stairs[facing=north,half=top]`.
- Compress runs of identical blocks along +x into one `fill x y z x2 y z block` (1-D run-length only). Single blocks may be `setblock`.
- Deterministic ordering: ascending y, then z, then x (so walls rise from the ground in the video).
- Never exceed 32,768 blocks per `fill` (impossible with 1-D runs, but assert).

```python
def backup_commands(box, slot: int) -> list[str]
def restore_commands(box, slot: int) -> list[str]
def clear_commands(box) -> list[str]
```
- `box = (x0,y0,z0,x1,y1,z1)` inclusive world coords. `slot` selects a storage area for `/clone` backups:
  storage origin = `(100000 + slot*256, 200, 100000)`; the box is cloned there with `clone x0 y0 z0 x1 y1 z1 sx sy sz replace force`.
  If the box exceeds 32,768 blocks, tile it into sub-boxes (chunks of ≤ 32 x 32 x 32) and emit one clone per tile; restore is the inverse.
- All of backup/restore/build must be wrapped in `forceload add`/`forceload remove` for both the site box and the storage box (chunk coords = block // 16). Provide
```python
def forceload_commands(box, add: bool) -> list[str]
```
- `clear_commands(box)` = `fill ... air` tiled to ≤ 32,768 blocks (used for undo when no backup exists).
- `tellraw` helper: `def say(msg: str) -> str` → `tellraw @a {"text":"...","color":"gold"}` (JSON-escape).

### `rcon_batch.py` (top-level file, stdlib only, runs on the SERVER box with python3)
```
python3 rcon_batch.py --port 25576 --password-file ~/buildagent-server/.rcon-password [--progress-every 200] < commands.txt
```
- Reads one command per line from stdin, sends them sequentially over RCON (Source RCON protocol, TCP, localhost), prints `N ok, M failed` summary and each failed line with the server's response to stderr, exits 1 if any failed.
- Treat responses containing `Unknown`, `Incorrect`, `not loaded`, `Expected`, `too many`, `Cannot` as failure; treat empty response as success.
- Reference implementation of the wire protocol: `C:\Users\<user>\minecraft-server\scripts\rcon_client.py` if present locally, otherwise write from the protocol spec (packet = int32 length, int32 id, int32 type(3=auth, 2=command), payload, 2 null bytes). Handle multi-packet responses by sending a trailing empty command and reading until its response arrives.
- Sends `--progress-every N` lines a `tellraw @a` progress message automatically (optional).

### `mcbuild/runner.py`
```python
@dataclass
class ServerConfig:  # loaded from mcbuild/server.toml (create the file with placeholders)
    ssh_host: str = "claude@minecraft-server"
    remote_dir: str = "~/buildagent-server"
    rcon_port: int = 25576
    password_file: str = "~/buildagent-server/.rcon-password"
    log_path: str = "~/buildagent-server/logs/latest.log"
def run_commands(cmds: list[str], cfg: ServerConfig) -> RunResult   # RunResult(ok: int, failed: list[tuple[str,str]], seconds: float)
def deploy_batch_script(cfg)   # scp rcon_batch.py to remote_dir (idempotent)
def rcon_one(cmd: str, cfg) -> str   # single command via ssh, returns response text (used by survey)
```
- Transport: `ssh <host> "python3 <remote_dir>/rcon_batch.py --port .. --password-file .."` with the commands piped on stdin. One ssh session per batch.
- Must work from Git Bash and PowerShell on Windows (use `subprocess.run` with a list argv, no shell).

## Layer 3: chat bridge (owner: implementation agent B)
### `mcbuild/bridge.py`
```
python -m mcbuild.bridge --config mcbuild/server.toml --workdir <dir with AGENTS.md> [--dry-run]
```
- Tails the server log over ssh: `ssh <host> tail -n 0 -F <log_path>`; parses chat lines of the form
  `[HH:MM:SS INFO]: <Player> !build <text>` (also `!modify`, `!undo`, `!yes`, `!no`). Ignore everything else. Regex must tolerate Paper's `[Not Secure]` prefix and thread names: match `<(\w+)> (!\w+)(.*)$`.
- For `!build` / `!modify`: runs
  `codex exec -m gpt-6-astra --skip-git-repo-check -C <workdir> -c model_reasoning_effort=medium --json "<prompt>"`
  where `<prompt>` = the player text plus the fixed prefix in `mcbuild/prompts/turn_prefix.txt` (create with a placeholder). The codex binary path comes from env `CODEX_BIN`, default `%LOCALAPPDATA%\OpenAI\Codex\bin\7ac07f4ce733f89a\codex.exe`; fall back to `codex` on PATH.
- Parses the `--json` event stream (JSONL on stdout): collect the final agent message text; on completion, send `tellraw @a` with the first 200 chars of it via `runner.rcon_one`. On failure send a red tellraw with the error.
- Serializes requests: one codex run at a time; queue further chat lines; a `!cancel` line kills the running codex process.
- `--dry-run`: print the codex command line instead of running it, and print tellraw JSON instead of sending.
- Keep a `bridge.log` with timestamps.
- Tests: parser tests for the log regex with real Paper log samples (include `[12:34:56 INFO]: <ULLAFNC> !build a small chapel` and `[12:34:56 INFO]: [Not Secure] <ULLAFNC> !undo`), and a JSONL parsing test using a sample codex `--json` output (record one with `codex exec --json "say hi"` if the binary exists; otherwise craft a plausible sample AND mark the test as needing a real recording).

## Ground truth facts
- Server box: Ubuntu, reachable as `ssh claude@minecraft-server` (key auth, no password) over Tailscale. `python3` present. Existing RCON client for reference on the box: `~/minecraft-server/scripts/rcon_client.py`.
- The demo server (Paper 1.21.8) is being set up NOW by another agent; ports may end up 25566/25576 or 25565/25575. Read them from `server.toml`, never hardcode.
- Ground level on the demo world is y = 0 (grass_block at y 0, air at y 1).
- Chunks must be force-loaded before placing; otherwise RCON answers `That position is not loaded`.
