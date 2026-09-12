"""Block-family palette: maps semantic roles (primary/secondary/accent/...) to concrete
vanilla block ids and their stairs/slab/wall/fence/trapdoor/door/log variants.

Pure, deterministic, no I/O. Minecraft 1.21.8 Java ids only, no `minecraft:` prefix.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Palette", "FAMILIES", "variant"]


@dataclass(frozen=True)
class Palette:
    primary: str = "calcite"            # wall body
    secondary: str = "polished_diorite"  # stairs/slabs/walls detail family
    accent: str = "deepslate_bricks"    # arches, pillars, outlines
    trim: str = "pale_oak"              # fences, trapdoors, doors (wood species)
    glass: str = "white_stained_glass_pane"
    roof: str = "deepslate_tiles"       # roof stairs family
    light: str = "end_rod"


def _stone_family(base: str, stairs: str | None, slab: str | None, wall: str | None) -> dict[str, str]:
    fam: dict[str, str] = {"block": base}
    if stairs is not None:
        fam["stairs"] = stairs
    if slab is not None:
        fam["slab"] = slab
    if wall is not None:
        fam["wall"] = wall
    return fam


# base block id -> {"block", "stairs", "slab", "wall"} (missing keys allowed when the
# vanilla variant does not exist).
FAMILIES: dict[str, dict[str, str]] = {
    "stone_bricks": _stone_family("stone_bricks", "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"),
    "deepslate_bricks": _stone_family(
        "deepslate_bricks", "deepslate_brick_stairs", "deepslate_brick_slab", "deepslate_brick_wall"
    ),
    "deepslate_tiles": _stone_family(
        "deepslate_tiles", "deepslate_tile_stairs", "deepslate_tile_slab", "deepslate_tile_wall"
    ),
    "polished_deepslate": _stone_family(
        "polished_deepslate", "polished_deepslate_stairs", "polished_deepslate_slab", "polished_deepslate_wall"
    ),
    "calcite": _stone_family("calcite", None, None, None),
    # Vanilla has no polished_diorite_wall / polished_andesite_wall / polished_granite_wall;
    # the cathedral reference maps the polished variant's wall detail onto the rough
    # variant's wall (diorite_wall / andesite_wall / granite_wall).
    "polished_diorite": _stone_family("polished_diorite", "polished_diorite_stairs", "polished_diorite_slab", "diorite_wall"),
    "diorite": _stone_family("diorite", "diorite_stairs", "diorite_slab", "diorite_wall"),
    "andesite": _stone_family("andesite", "andesite_stairs", "andesite_slab", "andesite_wall"),
    "polished_andesite": _stone_family(
        "polished_andesite", "polished_andesite_stairs", "polished_andesite_slab", "andesite_wall"
    ),
    "granite": _stone_family("granite", "granite_stairs", "granite_slab", "granite_wall"),
    "polished_granite": _stone_family(
        "polished_granite", "polished_granite_stairs", "polished_granite_slab", "granite_wall"
    ),
    "tuff_bricks": _stone_family("tuff_bricks", "tuff_brick_stairs", "tuff_brick_slab", "tuff_brick_wall"),
    "polished_tuff": _stone_family(
        "polished_tuff", "polished_tuff_stairs", "polished_tuff_slab", "polished_tuff_wall"
    ),
    "bricks": _stone_family("bricks", "brick_stairs", "brick_slab", "brick_wall"),
    "quartz_block": _stone_family("quartz_block", "quartz_stairs", "quartz_slab", None),
    "smooth_quartz": _stone_family("smooth_quartz", "smooth_quartz_stairs", "smooth_quartz_slab", None),
    "sandstone": _stone_family("sandstone", "sandstone_stairs", "sandstone_slab", "sandstone_wall"),
    "smooth_sandstone": _stone_family("smooth_sandstone", "smooth_sandstone_stairs", "smooth_sandstone_slab", None),
    "red_sandstone": _stone_family("red_sandstone", "red_sandstone_stairs", "red_sandstone_slab", "red_sandstone_wall"),
    "blackstone": _stone_family("blackstone", "blackstone_stairs", "blackstone_slab", "blackstone_wall"),
    "polished_blackstone_bricks": _stone_family(
        "polished_blackstone_bricks",
        "polished_blackstone_brick_stairs",
        "polished_blackstone_brick_slab",
        "polished_blackstone_brick_wall",
    ),
    "mud_bricks": _stone_family("mud_bricks", "mud_brick_stairs", "mud_brick_slab", "mud_brick_wall"),
    "cobblestone": _stone_family("cobblestone", "cobblestone_stairs", "cobblestone_slab", "cobblestone_wall"),
    "mossy_stone_bricks": _stone_family(
        "mossy_stone_bricks", "mossy_stone_brick_stairs", "mossy_stone_brick_slab", "mossy_stone_brick_wall"
    ),
    "prismarine_bricks": _stone_family("prismarine_bricks", "prismarine_brick_stairs", "prismarine_brick_slab", None),
    "dark_prismarine": _stone_family("dark_prismarine", "dark_prismarine_stairs", "dark_prismarine_slab", None),
    "nether_bricks": _stone_family("nether_bricks", "nether_brick_stairs", "nether_brick_slab", "nether_brick_wall"),
    "red_nether_bricks": _stone_family(
        "red_nether_bricks", "red_nether_brick_stairs", "red_nether_brick_slab", "red_nether_brick_wall"
    ),
    "end_stone_bricks": _stone_family(
        "end_stone_bricks", "end_stone_brick_stairs", "end_stone_brick_slab", "end_stone_brick_wall"
    ),
    "purpur_block": _stone_family("purpur_block", "purpur_stairs", "purpur_slab", None),
    "white_concrete": _stone_family("white_concrete", None, None, None),
    "smooth_stone": _stone_family("smooth_stone", None, "smooth_stone_slab", None),
    "cut_copper": _stone_family("cut_copper", "cut_copper_stairs", "cut_copper_slab", None),
    "oxidized_cut_copper": _stone_family(
        "oxidized_cut_copper", "oxidized_cut_copper_stairs", "oxidized_cut_copper_slab", None
    ),
}

# Wood species. Log block differs for a few species (crimson/warped -> "_stem",
# bamboo -> "bamboo_block" instead of a log).
_WOOD_SPECIES = [
    "oak",
    "spruce",
    "birch",
    "jungle",
    "acacia",
    "dark_oak",
    "mangrove",
    "cherry",
    "pale_oak",
    "bamboo",
    "crimson",
    "warped",
]
_LOG_OVERRIDE = {"bamboo": "bamboo_block", "crimson": "crimson_stem", "warped": "warped_stem"}

for _species in _WOOD_SPECIES:
    FAMILIES[_species] = {
        "planks": f"{_species}_planks",
        "stairs": f"{_species}_stairs",
        "slab": f"{_species}_slab",
        "fence": f"{_species}_fence",
        "trapdoor": f"{_species}_trapdoor",
        "door": f"{_species}_door",
        "log": _LOG_OVERRIDE.get(_species, f"{_species}_log"),
    }
del _species


def variant(pal: Palette, role: str, kind: str) -> str:
    """Return the block id for `kind` (block/stairs/slab/wall/planks/fence/trapdoor/door/log)
    of the family assigned to `role` (primary/secondary/accent/trim/glass/roof/light).

    Falls back through primary -> secondary -> accent -> stone_brick_* when the family
    assigned to `role` does not define `kind` (e.g. calcite has no stairs).
    """
    base = getattr(pal, role)
    fam = FAMILIES.get(base, {})
    if kind in fam:
        return fam[kind]
    for fallback_role in ("primary", "secondary", "accent"):
        fb_base = getattr(pal, fallback_role)
        fb_fam = FAMILIES.get(fb_base, {})
        if kind in fb_fam:
            return fb_fam[kind]
    if kind == "block":
        return "stone_bricks"
    return f"stone_brick_{kind}"
