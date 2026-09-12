# Harness prompt (v2, 2026-09-12)

Identical to plain_astra/prompt_v1.md except the Deliverable section: the output is a build.py using the mcbuild DSL, and the agent must read AGENTS.md (builder principles) and DSL_REFERENCE.md first. Same six photos attached.

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

Deliverable: write ONE Python 3.12 file `build.py` in the current directory defining
`def build() -> Build` using the mcbuild builder DSL. Before writing anything, read `AGENTS.md`
(the master builder's principles) and `DSL_REFERENCE.md` (the helper functions) in this directory
and follow both. The helpers embed the placements of the builder's reference cathedral; use them for
every wall, window, door, pillar, buttress, eave, plinth, beam, roof and spire, and use raw `box`/`put`
only for what they cannot express.
- Use `Build(origin=(-60, 1, 0), palette=Palette(...))`: choose the palette yourself for the white
  walls, dark spires, terracotta-red roof and stained glass described above (see the family list in
  DSL_REFERENCE.md; the roof family must have stairs).
- Ground is y = 0 (grass). Local y = 0 is the floor level. The west front faces -z; all local
  coordinates non-negative.
- Check your work with `cd "C:\Users\<user>\mcbuild" && python -m mcbuild.preview
  experiments/harness_astra/build.py --faces n,e,s,w` (ASCII elevations + `check()` warnings) and
  iterate until there are no warnings and the elevations match the photos' proportions.
Do not write any other files and do not explain in prose; the file is the answer.
