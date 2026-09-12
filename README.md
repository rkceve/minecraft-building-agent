# mcbuild — a Minecraft building agent that builds like a master builder

AI Tinkerers Global Hackathon, 2026-09-12. Theme: *Agents, Everywhere: Beyond the Chatbox*.

A player types `!build a small gothic church ...` in Minecraft chat. GPT-6 Astra designs the
building, a harness made of the builder's own principles and the builder's own cathedral turns that
design into block-level detail, and the building rises in the live world over RCON. The player then
walks around it and says `!fix make this tower taller` while looking at the tower; only the changed
blocks are replaced, in place, while they watch.

## What is new here

LLMs can already lay out 3D massing. What they cannot do is place blocks the way an experienced
Minecraft builder does. mcbuild puts a **harness** between the model and the world:

1. **Spoken harness** — `mcbuild/prompts/AGENTS.md`: the builder's principles (odd widths and one
   axis, windows with depth, pillars as the skeleton, stairs-only roofs, no flat walls, a foundation
   scaled to the building). Written by the builder in Japanese, translated to English.
2. **Coded harness** — `mcbuild/dsl.py` + `mcbuild/techniques.py`: small helper functions
   (`window`, `corner_pillar`, `eave`, `gable_roof`, `buttress`, `plinth`, `beam`, `spire`, ...)
   whose bodies encode the placements read from the builder's reference cathedral
   (`refs/cathedral.litematic`, 186 x 109 x 81, 64k blocks, by ULLAFNC). The LLM never writes block
   states or palette variants; it composes these helpers.

Astra writes a `build.py` that calls the DSL. A fix request is a code edit; the world update is a
voxel diff.

## Before / after (same photos, same prompt, harness added)

| | plain Astra | Astra + harness |
|---|---|---|
| prompt | `experiments/plain_astra/prompt_v1.md` | `experiments/harness_astra/prompt_v2.md` (v1 + "read AGENTS.md and DSL_REFERENCE.md, write with the DSL") |
| output | `experiments/plain_astra/church_plain.py` (raw voxel dict) | `experiments/harness_astra/build.py` (DSL script) |
| blocks | 9,294 | 10,095 |
| width | 30 | 29 (odd, per the builder's rule) |

Subject: the Old Catholic Shimizu Church (Shizuoka, Japan, wooden Gothic, 1935, demolished 2024)
at 2:1 scale, from six photos.

## Architecture

```
Minecraft chat  --ssh tail-->  bridge.py  --codex exec (GPT-6 Astra)-->  edits builds/<id>/build.py
                                    |                                          |
                                    |<-- preview.py (ASCII elevations, check()) <-+
                                    v
                             apply.py: diff old/new voxels -> fill/setblock over RCON (rcon_batch.py on the server)
```

- `mcbuild/bridge.py` — tails the Paper server log, parses `!build` / `!fix` / `!undo` / `!status` /
  `!cancel`, gathers player context (position, facing, the element the player is looking at via a
  voxel raycast against the build's provenance map), runs `codex exec -m gpt-6-astra` non-interactively
  (ChatGPT Plus login, no API key), then previews and applies.
- `mcbuild/dsl.py`, `techniques.py`, `palette.py`, `blockstate.py` — the coded harness. Every element
  call is tagged, so "this window" resolves to an element id like `nave_w_lancet_21`.
- `mcbuild/apply.py`, `emit.py`, `runner.py`, `rcon_batch.py` — realization: run-length `fill`
  compression, `/clone` backup for undo, forceload handling, streamed at a chosen commands/second so
  the building visibly rises.
- `mcbuild/player.py` — `data get entity` pose, view vector, Amanatides–Woo raycast, ground target.
- `mcbuild/litematic.py`, `ascii.py` — reading the reference schematic, ASCII elevations used both by
  humans and by Astra to check its own work.

## Running it

Server: Paper 1.21.8, flat world with ground at y=0, RCON enabled, creative. Fill `mcbuild/server.toml`.

```
pip install nbtlib numpy pytest ruff
python -m pytest -q                      # 107+ tests, no server needed
python -m mcbuild.runner --deploy        # copy rcon_batch.py to the server box
python -m mcbuild.preview tests/fixtures/chapel.py --faces n,e
python -m mcbuild.bridge --build-id church --rate 60
```
Then in game: `!build a small gothic church`, `!fix make the spires taller`, `!undo`.

## Honest notes

- The reference cathedral schematic is a pre-existing asset by the builder. All code was written on
  hackathon day (Claude Code with Sonnet/Fable agents implementing against `DSL.md` / `CONTRACT.md`).
- The coded harness encodes the cathedral's grammar (pointed-arch stepping, relief frames, ringed
  piers with bands and pinnacles, inverted-stair eaves, ridge ornaments). Work in progress:
  stamping the cathedral's actual window tracery instead of a parametric approximation
  (`mcbuild/stamps.py`).
- Astra turn time is 1–4 minutes per request; the world update takes seconds.
- Related work: Voyager / Mindcraft-style agents drive a bot; mcbuild is server-side (no bot),
  and its contribution is the harness layer, not the agent loop.

## Credits

Builder and principles: Ryosuke Kawai (ULLAFNC). Design LLM: GPT-6 Astra via Codex CLI.
Implementation: Claude Code.
