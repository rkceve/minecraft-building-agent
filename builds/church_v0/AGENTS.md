# Builder's principles — Gothic architecture (hackathon harness prompt)

Written by ULLAFNC (the builder whose cathedral is the sample). Translated from Japanese.
"The sample" below means the reference cathedral (`refs/cathedral.litematic`). Its placements are
encoded in the `mcbuild.dsl` helper functions; when a principle says "see the sample", use the helper
named in brackets instead of inventing your own block arrangement.

1. **Odd widths, one axis.** Make the building's width an odd number of blocks so there is a true centre
   column. Keep both the exterior and the interior symmetric about that centre axis, and keep that axis
   consistent through the whole building.

2. **Windows have depth.** Wall windows follow the sample: they are not holes with glass, they have an
   outline, a relief frame one block proud of the wall, a sill, and tracery. Give them three-dimensional
   relief. [`Build.window` / `Build.windows`]

3. **Tower roofs taper naturally.** A tower's roof narrows to a point as smoothly as the sample's spires
   do, not in abrupt jumps. [`Build.spire`]

4. **Pillars are the skeleton.** Pillar positions must line up vertically from the foundation to the top:
   a pillar on an upper level stands on a pillar below it. Think about how real Gothic pillars and
   buttresses carry the building's load, and let that structure show. Beams are not just laid across a
   span: add arches (braces) at their ends so they visibly carry the load into the pillars. The sample
   shows how this is done in Minecraft. [`Build.corner_pillar`, `Build.buttress`, `Build.beam`]

5. **Roofs are stairs only.** Build roofs from stair blocks laid diagonally, as in the sample, nothing
   else in the slope. With an odd building width the topmost row of the roof is exactly one block wide;
   decorate that ridge row the way the sample does. [`Build.gable_roof` — the ridge ornament is applied
   automatically when the span is odd]

6. **Walls must not be flat.** Add detail to every wall face so no large area reads as a plain slab:
   pilasters, plinth and string courses, recessed panels. Add detail the way the sample does.
   [`Build.wall` with `depth=True`, `Build.room`]

7. **Every building has a foundation.** Give the building a base (plinth) scaled to its size, and connect
   the vertical pillars into it so the structure reads as one piece from the ground up. Details as in the
   sample. [`Build.room(plinth=...)`, `Build.plinth`]

Working rules for this workspace:
- Use the helpers from `mcbuild.dsl` for every element they cover; use raw `box`/`put` only for things
  the helpers cannot express (and keep those symmetric about the axis).
- Preview with `python -m mcbuild.preview build.py --faces n,e,s,w` and fix every `check()` warning.
- Choose one palette of at most three material families (primary / secondary / accent) plus one wood
  species for trim, one glass, one roof family. Do not mix more.
