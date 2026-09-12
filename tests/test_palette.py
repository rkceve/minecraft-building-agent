import re

import pytest

from mcbuild.palette import FAMILIES, Palette, variant

_ID_RE = re.compile(r"^[a-z0-9_]+$")

_WOOD_SPECIES = [
    "oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove",
    "cherry", "pale_oak", "bamboo", "crimson", "warped",
]

_REQUIRED_STONE_FAMILIES = [
    "stone_bricks", "deepslate_bricks", "deepslate_tiles", "polished_deepslate", "calcite",
    "polished_diorite", "diorite", "andesite", "polished_andesite", "granite", "polished_granite",
    "tuff_bricks", "polished_tuff", "bricks", "quartz_block", "smooth_quartz", "sandstone",
    "smooth_sandstone", "red_sandstone", "blackstone", "polished_blackstone_bricks", "mud_bricks",
    "cobblestone", "mossy_stone_bricks", "prismarine_bricks", "dark_prismarine", "nether_bricks",
    "red_nether_bricks", "end_stone_bricks", "purpur_block", "white_concrete", "smooth_stone",
    "cut_copper", "oxidized_cut_copper",
]


def test_required_stone_families_present():
    for base in _REQUIRED_STONE_FAMILIES:
        assert base in FAMILIES, f"missing family {base}"


def test_required_wood_families_present():
    for species in _WOOD_SPECIES:
        assert species in FAMILIES, f"missing wood family {species}"
        fam = FAMILIES[species]
        for kind in ("planks", "stairs", "slab", "fence", "trapdoor", "door", "log"):
            assert kind in fam, f"{species} missing {kind}"


def test_all_family_ids_match_naming_rules():
    for base, fam in FAMILIES.items():
        for kind, block_id in fam.items():
            assert _ID_RE.match(block_id), f"{base}.{kind} = {block_id!r} has invalid chars"
            if kind == "stairs":
                assert block_id.endswith("_stairs"), f"{base}.stairs = {block_id!r}"
            elif kind == "slab":
                assert block_id.endswith("_slab"), f"{base}.slab = {block_id!r}"
            elif kind == "wall":
                assert block_id.endswith("_wall"), f"{base}.wall = {block_id!r}"


def test_wood_log_overrides():
    assert FAMILIES["bamboo"]["log"] == "bamboo_block"
    assert FAMILIES["crimson"]["log"] == "crimson_stem"
    assert FAMILIES["warped"]["log"] == "warped_stem"
    assert FAMILIES["oak"]["log"] == "oak_log"


def test_variant_direct_hit():
    pal = Palette()
    assert variant(pal, "secondary", "stairs") == "polished_diorite_stairs"
    assert variant(pal, "accent", "wall") == "deepslate_brick_wall"
    assert variant(pal, "trim", "fence") == "pale_oak_fence"
    assert variant(pal, "trim", "door") == "pale_oak_door"


def test_variant_polished_diorite_wall_maps_to_diorite_wall():
    pal = Palette()
    assert variant(pal, "secondary", "wall") == "diorite_wall"


def test_variant_fallback_primary_has_no_stairs():
    pal = Palette()  # primary = calcite, no stairs
    assert variant(pal, "primary", "stairs") == variant(pal, "secondary", "stairs")
    assert variant(pal, "primary", "stairs") == "polished_diorite_stairs"


def test_variant_ultimate_fallback_stone_brick():
    pal = Palette(primary="calcite", secondary="calcite", accent="calcite")
    assert variant(pal, "primary", "stairs") == "stone_brick_stairs"
    assert variant(pal, "primary", "wall") == "stone_brick_wall"
    # calcite's own family DOES define "block" (= itself), so no fallback happens here.
    assert variant(pal, "primary", "block") == "calcite"


@pytest.mark.parametrize("species", _WOOD_SPECIES)
def test_variant_wood_roles(species):
    pal = Palette(trim=species)
    assert variant(pal, "trim", "planks") == FAMILIES[species]["planks"]
    assert variant(pal, "trim", "stairs") == FAMILIES[species]["stairs"]
    assert variant(pal, "trim", "slab") == FAMILIES[species]["slab"]
    assert variant(pal, "trim", "log") == FAMILIES[species]["log"]
