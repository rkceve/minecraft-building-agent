"""Old Catholic Shimizu Church, two blocks per metre; west is local -z."""

from dataclasses import replace

from mcbuild.dsl import Build
from mcbuild.palette import Palette


def build() -> Build:
    # White quartz render, diorite dressings, dark deepslate metalwork;
    # brick roof tiles, dark-oak joinery and a single violet glass.
    pal = Palette(
        primary="smooth_quartz",
        secondary="smooth_quartz",
        accent="diorite",
        trim="dark_oak",
        glass="purple_stained_glass_pane",
        roof="bricks",
        light="end_rod",
    )
    b = Build(origin=(-60, 1, 0), palette=pal, seed=1935)
    # The principal masses share x=14. The photographed low side annex
    # is the sole deliberate exception to bilateral symmetry.
    b.plinth(2, 3, 26, 10, 0, height=1, projection=1, id="porch_foundation")
    b.plinth(5, 10, 23, 39, 0, height=1, projection=1, id="nave_foundation")
    b.floor(2, 2, 26, 10, 0, id="porch_paving")
    b.floor(5, 10, 23, 39, 0, id="nave_floor")

    nave = {}
    nave["w"] = b.wall("w", 5, 11, 5, 39, 1, 12, bay=7, id="nave_west_side")
    nave["e"] = b.wall("e", 23, 11, 23, 39, 1, 12, bay=7, id="nave_east_side")
    nave["s"] = b.wall("s", 5, 39, 23, 39, 1, 12, bay=6, id="chancel_wall")
    entrance = b.wall("n", 2, 10, 26, 10, 1, 12, bay=8, id="recessed_entrance")
    porch = b.wall("n", 2, 3, 26, 3, 1, 8, bay=8, id="three_arch_arcade")
    porch_sides = [
        b.wall("w", 2, 3, 2, 10, 1, 8, bay=7, id="porch_return_w"),
        b.wall("e", 26, 3, 26, 10, 1, 8, bay=7, id="porch_return_e"),
    ]
    gallery = b.wall("n", 2, 3, 26, 3, 9, 10, bay=8, id="rose_gallery")
    gallery_returns = [
        b.wall("w", 2, 3, 2, 10, 9, 10, bay=7, id="gallery_return_w"),
        b.wall("e", 26, 3, 26, 10, 9, 10, bay=7, id="gallery_return_e"),
        b.wall("s", 2, 10, 26, 10, 13, 6, bay=8, id="gallery_rear"),
    ]

    # Use the door helper's pointed stone openings, removing only the
    # door leaves to make the photograph's open, walk-through arcade.
    for u, width, height, name in ((2, 5, 7, "right"), (9, 7, 8, "centre"), (18, 5, 7, "left")):
        b.door(porch, u=u, width=width, height=height, id=f"arcade_{name}")
        x0, _, z0 = porch.world(u + width - 1, 0)
        x1, _, _ = porch.world(u, 0)
        b.clear(x0, 1, z0, x1, 2, z0)
    for i, frame in enumerate(porch_sides):
        u = 2 if frame.face == "w" else 3
        b.door(frame, u=u, width=3, height=6, id=f"porch_side_arch_{i}")
        p0, p1 = frame.world(u, 0), frame.world(u + 2, 1)
        b.clear(*p0, *p1)
    b.door(entrance, u=11, width=3, height=6, id="main_oak_door")
    for u in (3, 19):
        b.window(entrance, u, 2, 3, 7, id=f"entrance_lancet_{u}")
    b.window(gallery, 9, 2, 7, 7, style="rose", id="great_west_rose")
    for u in (3, 19):
        b.window(gallery, u, 2, 3, 6, id=f"facade_lancet_{u}")
    for frame in gallery_returns[:2]:
        u = 2 if frame.face == "w" else 3
        b.window(frame, u, 2, 3, 6, id=f"gallery_side_lancet_{frame.face}")
    for u in (3, 5, 19, 21):
        b.window(porch, u, 6, 1, 1, style="rose", id=f"porch_oculus_{u}")

    # Four tall bays and small high-level round lights on each nave side.
    # World-z placement is shared, including the structural pier lines.
    for face in ("w", "e"):
        frame = nave[face]
        for z in (14, 21, 28, 35):
            u = z - 11 - 1 if face == "w" else 39 - z - 1
            b.window(frame, u, 2, 3, 7, id=f"nave_{face}_lancet_{z}")
            for dz in (-1, 1):
                uc = z + dz - 11 if face == "w" else 39 - z - dz
                b.window(frame, uc, 10, 1, 1, style="rose", id=f"clerestory_{face}_{z}_{dz}")
        for z in (11, 18, 25, 32, 39):
            u = z - 11 if face == "w" else 39 - z - 1
            b.buttress(frame, u, depth=1, height=11, id=f"nave_{face}_buttress_{z}")
        b.eave(frame, id=f"nave_{face}_cornice")
    b.window(nave["s"], 7, 3, 5, 7, id="east_chancel_window")
    b.eave(nave["s"], id="chancel_cornice")
    for i, frame in enumerate([porch, *porch_sides]):
        b.eave(frame, id=f"porch_string_course_{i}")
    for i, frame in enumerate([gallery, *gallery_returns]):
        b.eave(frame, id=f"upper_cornice_{i}")

    # A blind-arcaded parapet joins the two square bell stages.
    frieze = b.wall("n", 2, 3, 26, 3, 18, 2, bay=2, id="ornamented_frieze")
    b.eave(frieze, id="frieze_coping")
    for x in range(3, 26, 2):
        # Tiny projecting trefoil-like ornaments have no separate DSL helper.
        b.put(x, 19, 2, "diorite_wall", id=f"frieze_ornament_{x}")

    bell_stages = []
    for x0, name in ((3, "left"), (19, "right")):
        frames = b.room(x0, 3, x0 + 6, 9, 19, 5,
                        pillars=False, eaves=True, plinth=False, id=f"belfry_{name}")
        bell_stages.append((x0, name))
        for face, frame in frames.items():
            b.window(frame, 2, 2, 3, 3, id=f"belfry_{name}_{face}_opening")
            # Open oak shutters suggest the dark horizontal bell louvers.
            for u in range(2, 5):
                for v in (2, 3):
                    x, y, z = frame.world(u, v)
                    facing = {"n": "north", "s": "south", "e": "east", "w": "west"}[face]
                    b.put(x, y, z, f"dark_oak_trapdoor[facing={facing},half=bottom,open=true,powered=false]",
                          id=f"louver_{name}_{face}_{u}_{v}")
        for x in (x0, x0 + 6):
            for z in (3, 9):
                b.corner_pillar(x, z, 0, 24, size=1, id=f"continuous_tower_pier_{x}_{z}")

    # Low red-tiled sacristy on the photographed right side.
    annex = b.room(22, 19, 26, 37, 0, 7, pillars=False,
                   plinth=False, id="side_sacristy")
    b.plinth(22, 19, 26, 37, 0, height=1, projection=1, id="sacristy_base")
    b.floor(22, 19, 26, 37, 0, id="sacristy_floor")
    for u in (3, 10):
        b.window(annex["e"], u, 2, 3, 4, id=f"sacristy_window_{u}")
    partition = b.wall("w", 22, 19, 22, 37, 1, 6, thickness=2,
                       bay=6, id="sacristy_partition")
    b.door(partition, u=8, width=3, height=5, id="sacristy_access")
    b.gable_roof(22, 19, 26, 37, 7, ridge="z", overhang=1, id="red_sacristy_roof")

    # A narrower rear chancel continues the one centre axis.
    apse = b.room(9, 39, 19, 44, 0, 8, pillars=False,
                  plinth=False, id="rear_chancel")
    b.plinth(9, 39, 19, 44, 0, height=1, projection=1, id="rear_chancel_base")
    b.floor(9, 39, 19, 44, 0, id="rear_chancel_floor")
    b.window(apse["s"], 4, 2, 3, 5, id="rear_chancel_lancet")
    chancel_entry = b.wall("n", 9, 39, 19, 39, 1, 7, thickness=1,
                           bay=10, id="chancel_arch_wall")
    b.door(chancel_entry, u=4, width=3, height=6, id="chancel_arch")
    b.clear(13, 1, 39, 15, 2, 39)
    b.gable_roof(9, 39, 19, 44, 8, ridge="z", overhang=1, id="red_chancel_roof")
    b.gable_roof(5, 10, 23, 39, 13, ridge="z", overhang=1, id="red_nave_roof")

    # Spires reuse the dark masonry family; nave tiles retain the sole red
    # roof family. All slopes and the taper come from the reference helpers.
    b.palette = replace(pal, roof="deepslate_tiles")
    for x0, name in bell_stages:
        b.spire(x0, 3, x0 + 6, 9, 24, 7, id=f"dark_spire_{name}")
        cx = x0 + 3
        # Cross arms are the only custom spire geometry.
        b.box(cx - 1, 32, 6, cx + 1, 32, 6, "deepslate_tile_wall", id=f"cross_{name}")
        b.put(cx, 33, 6, "deepslate_tile_wall", id=f"cross_tip_{name}")
    b.palette = pal

    # Gallery floor, load-bearing interior posts, and braced timber ties.
    b.floor(3, 4, 25, 9, 9, id="organ_gallery_floor")
    for z in (18, 25, 32, 38):
        for x in (6, 22):
            b.corner_pillar(x, z, 0, 10, size=1, id=f"interior_post_{x}_{z}")
        b.beam(6, z, 22, z, 12, braces=True, id=f"nave_braced_tie_{z}")
    # Furniture has no dedicated DSL helper. Keep seating mirrored.
    for z in (15, 18, 21, 24, 27, 30):
        for xa, xb in ((8, 11), (17, 20)):
            b.box(xa, 1, z, xb, 1, z, "dark_oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]",
                  id=f"pew_{xa}_{z}")
    b.box(12, 1, 36, 16, 2, 37, "smooth_quartz", id="altar")
    b.box(14, 3, 38, 14, 7, 38, "dark_oak_fence", id="altar_cross_stem")
    b.box(12, 6, 38, 16, 6, 38, "dark_oak_fence", id="altar_cross_arms")
    return b
