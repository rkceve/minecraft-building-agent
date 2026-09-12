# Plain-Astra baseline prompt (v1, 2026-09-12)

This is the exact prompt given to GPT-6 Astra (via `codex exec -m gpt-6-astra`) with the six reference
photos in `refs/shimizu/` attached. No building-technique harness, no reference schematic: this is the
"before" baseline. Photos: Old Catholic Shimizu Church, Shizuoka, Japan (wooden Gothic, 1935, demolished 2024).

---

You are an experienced Minecraft builder. Recreate the church shown in the attached photos in Minecraft
Java Edition 1.21.8 at 2:1 scale (1 real metre = 2 blocks).

Facts about the real building (Old Catholic Shimizu Church, Shizuoka, Japan, built 1935, wooden Gothic):
- Footprint about 13 m wide x 22 m deep; overall height about 15 m (spire tips). At 2:1 that is roughly
  26 blocks wide, 44 blocks deep, 30 blocks tall. Stay within 30 x 50 footprint and 34 height.
- Twin square towers flanking the west front, each topped by a steep dark pyramidal spire with a cross.
- West front between the towers: three pointed-arch openings at ground level (arcade porch), a large rose
  window above, a frieze band with small ornaments between first and second floor, small round windows.
- Nave with a red-tiled gable roof; a lower side aisle / annex along one side, also red-tiled.
- Tall pointed-arch stained-glass windows along the nave sides, with clerestory windows above.
- Walls are white (rendered wood). Spires dark grey/black. Roof terracotta red.

Deliverable: write ONE Python 3.12 file `church_plain.py` in the current directory, stdlib only, defining
`def build() -> dict[tuple[int, int, int], str]` that returns a voxel dictionary
`{(x, y, z): "block_name[prop=val,...]"}`.
- Use Java Edition block ids without the `minecraft:` prefix, with correct block-state properties for
  stairs (facing, half, shape), slabs (type), walls, fences, logs (axis), trapdoors (facing, half, open).
- Ground is y = 0 (grass). Put the floor at y = 1. The building's west front faces -z (north in
  Minecraft terms is fine; just be consistent). Origin corner at (0, 1, 0), all coordinates non-negative.
- Choose blocks yourself (e.g. white concrete / quartz / calcite / smooth quartz for walls,
  deepslate or blackstone stairs for spires, red terracotta / brick stairs for roofs, glass panes or
  stained glass for windows, dark oak for doors and trim, lanterns for lighting). Interior may be simple
  (floor, pews optional) but the shell must be complete, including a roof made of stairs with correct
  facing, and no floating or missing blocks.
- Do not store air. Add `if __name__ == "__main__": print(len(build()))`.
Run the file once to confirm it executes and prints a block count. Do not write any other files and do
not explain in prose; the file is the answer.
