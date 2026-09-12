# Minecraft build-agent demo server — requirements (hand to the Japan server agent)

Purpose: a throwaway creative server used today (2026-09-12) for a hackathon demo. A harness on <user>'s dev PC (Canada, on the same Tailscale network) places blocks over RCON and reads in-game chat from the server log over ssh. Nothing here touches the existing fincraft production server except port allocation.

## Must have
1. **Server software: Paper 1.21.8** (latest build for 1.21.8). Java 21.
   - Reason: the reference schematic (`cathedral.litematic`, DataVersion 4440) and the player's client (Fabric 1.21.8 + Litematica) are 1.21.8. Do NOT use 26.x; the client cannot join it.
   - Install in a separate directory (e.g. `~/buildagent-server`), not inside `~/server`.
2. **Ports**: if fincraft (25565 / RCON 25575) keeps running, use **25566** (game) and **25576** (RCON). If fincraft is stopped for the day, the default ports are fine. Report which ports were chosen.
   - Game port reachable from the player's client (Tailscale at minimum; public is optional).
   - RCON port reachable from the dev PC over Tailscale (ufw: allow on tailscale0 only). Never expose RCON publicly.
3. **server.properties**
   ```
   enable-rcon=true
   rcon.port=<see above>
   rcon.password=<generate, 24+ chars, store in ~/buildagent-server/.rcon-password mode 600>
   online-mode=true
   white-list=true
   enforce-whitelist=true
   gamemode=creative
   force-gamemode=true
   difficulty=peaceful
   spawn-protection=0
   view-distance=16
   simulation-distance=8
   max-players=5
   level-name=world
   level-type=minecraft\:flat
   generator-settings={"layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:stone","height":3},{"block":"minecraft:dirt","height":60},{"block":"minecraft:grass_block","height":1}],"biome":"minecraft:plains"}
   ```
   - The flat preset puts the grass surface at **y = 0** (65 layers starting at y = -64). The harness assumes ground = y 0 on this world. Confirm with `/execute if block 0 0 0 grass_block` → must succeed, and `/execute if block 0 1 0 air` → must succeed.
   - Delete any pre-generated `world/` before first start so the flat preset takes effect.
4. **Whitelist + op**: whitelist `<player>` and `op <player>` (level 4).
5. **Gamerules** (run once via console after first start):
   ```
   gamerule doDaylightCycle false
   gamerule doWeatherCycle false
   gamerule doMobSpawning false
   gamerule doFireTick false
   gamerule commandModificationBlockLimit 4000000
   gamerule spawnRadius 0
   time set 6000
   weather clear
   setworldspawn 0 1 0
   ```
6. **RCON check**: from the server box, `python3 rcon_batch.py-style client (or mcrcon) <rcon-port> $(cat ~/buildagent-server/.rcon-password) "forceload add 0 0"` then
   `... "setblock 0 5 0 oak_stairs[facing=north,half=top,shape=straight]"` → expect `Changed the block at 0, 5, 0`. Then `setblock 0 5 0 air` and `forceload remove 0 0`.
7. **ssh access for the dev PC** (already exists as `<ssh-user>@<server-host>`): the dev PC will run `tail -F ~/buildagent-server/logs/latest.log` over ssh to read chat, and will `scp` one small Python script (`rcon_batch.py`) into `~/buildagent-server/`. `python3` on the box is enough (stdlib only, no pip needed).
8. **Run as a systemd unit or a `screen`/`tmux` session** so it survives the ssh session. Report the start/stop command.
9. **EULA** accepted (<user> has accepted Mojang's EULA for this machine before; set `eula=true`).

## Nice to have (do only if it takes < 10 min)
- **WorldEdit plugin for Paper 1.21.8** (Bukkit build, `WorldEdit-Bukkit-7.3.x.jar`) so the player can paste the cathedral schematic in-game and use `//undo` manually. The harness does NOT depend on it.
- Pre-`forceload` the demo area: `forceload add -64 -64 128 128` (keeps chunks loaded so RCON placement never fails with "That position is not loaded").
- Chunk pre-generation is unnecessary on a flat world.

## Not needed
- No server-side mods (Fabric not required; the client's mods are client-only).
- No database, no Geyser/Floodgate, no Discord bridge, no web API.
- No backups (throwaway world).

## Report back
- Game host:port, RCON port, path of the RCON password file, log file path, start/stop command, and the output of the RCON check in item 6.
