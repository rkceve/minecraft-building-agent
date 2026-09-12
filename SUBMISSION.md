# Submission text

## Title
mcbuild — an in-game Minecraft building agent that builds like a master builder

## Description (portal)

Type `!build a small gothic church` in Minecraft chat and a church rises in the live world while you
watch. Walk up to a tower, look at it, and say `!fix make this tower taller`: only the changed blocks
are replaced, in place. No bot, no chatbox: the agent lives in the game server and in the builder's
own workflow.

The LLM (GPT-6 Astra via Codex CLI) is good at 3D massing but places blocks like a beginner. mcbuild
puts a harness between the model and the world, made of two things a master builder gave us:

1. **His principles as the system prompt** — odd widths and one axis, windows with real depth, pillars
   as the skeleton, stairs-only roofs, no flat walls, a foundation scaled to the building.
2. **His cathedral as code** — small helper functions (`window`, `corner_pillar`, `eave`, `gable_roof`,
   `buttress`, `plinth`, `beam`, `spire`) whose bodies encode the placements read from his 64,000-block
   reference cathedral, including a window style stamped directly from the schematic's tracery.

Astra composes these helpers into a build script; the harness resolves block states, palette variants
and detail. A fix request is a code edit, the world update is a voxel diff, and every element carries a
name so "this window" means the window you are looking at (position, view direction and a raycast
against the build are passed to the model each turn).

Before/after in the video: the same six photos of the Old Catholic Shimizu Church (Shizuoka, 1935) and
the same prompt, once with plain Astra and once with the harness. Then three live `!fix` turns:
roof raised, towers and spires raised, windows re-centred. Each turn takes 2–4 minutes of model time
and 6–50 seconds to land in the world.

Stack: Paper 1.21.8 server + RCON, Python harness (DSL, techniques, voxel diff, `/clone` undo), Codex
CLI non-interactive with a ChatGPT Plus login (no API key), Claude Code for implementation. All code was
written on hackathon day; the reference cathedral schematic and the builder's principles are the
builder's prior work.

Repo: https://github.com/rkceve/minecraft-building-agent

## Social post (X / LinkedIn)

Built for #AgentsEverywhere at the @aitinkerers Global Hackathon: a Minecraft building agent that
builds like a master builder. Chat in game, GPT-6 Astra designs, a harness made of the builder's
principles + his cathedral's block placements does the detail, and fixes land live as voxel diffs.
Repo: https://github.com/rkceve/minecraft-building-agent

(add the partner handles from the submission form)

## Short description (one line)
In-game Minecraft building agent: GPT-6 Astra designs, a master builder's principles and cathedral
placements become the harness, fixes land live as voxel diffs.
