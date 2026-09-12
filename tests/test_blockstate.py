from mcbuild.blockstate import (
    connect_fences_and_walls,
    door,
    fence,
    fix_stair_corners,
    log,
    pane,
    rotate_state,
    slab,
    stairs,
    stairs_toward,
    trapdoor,
    wall,
)


def test_stairs_basic_property_order_and_defaults():
    assert stairs("oak_stairs", "north") == "oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"
    assert stairs("oak_stairs", "east", half="top", shape="outer_left") == (
        "oak_stairs[facing=east,half=top,shape=outer_left,waterlogged=false]"
    )


def test_slab():
    assert slab("stone_brick_slab") == "stone_brick_slab[type=bottom,waterlogged=false]"
    assert slab("stone_brick_slab", "double") == "stone_brick_slab[type=double,waterlogged=false]"


def test_log():
    assert log("oak_log", "y") == "oak_log[axis=y]"
    assert log("oak_log", "x") == "oak_log[axis=x]"


def test_wall_defaults_and_sides():
    assert wall("stone_brick_wall") == (
        "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
    )
    out = wall("stone_brick_wall", up=False, north="low", east="tall")
    assert out == "stone_brick_wall[east=tall,north=low,south=none,up=false,waterlogged=false,west=none]"


def test_fence_bool_sides():
    assert fence("oak_fence") == "oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
    assert fence("oak_fence", north=True, south=True) == (
        "oak_fence[east=false,north=true,south=true,waterlogged=false,west=false]"
    )


def test_pane_bool_sides():
    assert pane("white_stained_glass_pane", north=True) == (
        "white_stained_glass_pane[east=false,north=true,south=false,waterlogged=false,west=false]"
    )


def test_trapdoor():
    assert trapdoor("pale_oak_trapdoor", "north") == (
        "pale_oak_trapdoor[facing=north,half=bottom,open=false,waterlogged=false]"
    )
    assert trapdoor("pale_oak_trapdoor", "south", half="top", open=True) == (
        "pale_oak_trapdoor[facing=south,half=top,open=true,waterlogged=false]"
    )


def test_door_no_waterlogged():
    # door is intentionally excluded from the auto waterlogged=false list (DSL.md blockstate.py section).
    assert door("pale_oak_door", "north", "lower") == "pale_oak_door[facing=north,half=lower,hinge=left,open=false]"
    assert door("pale_oak_door", "north", "upper", hinge="right", open=True) == (
        "pale_oak_door[facing=north,half=upper,hinge=right,open=true]"
    )


def test_stairs_toward_truth_table():
    # stairs_toward(block, face) builds a stair whose LOW step points toward `face`,
    # so vanilla `facing` (which points to the TALL side) is the opposite direction.
    assert stairs_toward("stone_stairs", "n") == "stone_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]"
    assert stairs_toward("stone_stairs", "s") == "stone_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"
    assert stairs_toward("stone_stairs", "e") == "stone_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]"
    assert stairs_toward("stone_stairs", "w") == "stone_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]"


def test_stairs_toward_half_top():
    assert stairs_toward("stone_stairs", "n", half="top") == (
        "stone_stairs[facing=south,half=top,shape=straight,waterlogged=false]"
    )


def test_rotate_state_facing_cycle():
    b = stairs("oak_stairs", "north")
    assert "facing=east" in rotate_state(b, 1)
    assert "facing=south" in rotate_state(b, 2)
    assert "facing=west" in rotate_state(b, 3)
    assert "facing=north" in rotate_state(b, 4)
    assert rotate_state(b, 0) == b


def test_rotate_state_axis():
    b = log("oak_log", "x")
    assert rotate_state(b, 1) == "oak_log[axis=z]"
    assert rotate_state(b, 2) == "oak_log[axis=x]"  # 180 degrees: axis unchanged
    assert rotate_state(b, 3) == "oak_log[axis=z]"
    b_y = log("oak_log", "y")
    assert rotate_state(b_y, 1) == "oak_log[axis=y]"  # vertical axis never rotates


def test_rotate_state_side_props_cycle():
    # north=true, everything else false/default. One CW turn: the value that was on the
    # north side should now describe the east side (see blockstate.py docstring derivation).
    b = fence("oak_fence", north=True)
    r1 = rotate_state(b, 1)
    assert r1 == "oak_fence[east=true,north=false,south=false,waterlogged=false,west=false]"
    r2 = rotate_state(b, 2)
    assert r2 == "oak_fence[east=false,north=false,south=true,waterlogged=false,west=false]"
    r4 = rotate_state(b, 4)
    assert r4 == b


def test_rotate_state_shape_and_hinge_unchanged():
    s = stairs("stone_stairs", "north", shape="outer_left")
    r = rotate_state(s, 1)
    assert "shape=outer_left" in r
    assert "facing=east" in r

    d = door("oak_door", "north", "lower", hinge="right")
    r = rotate_state(d, 1)
    assert "hinge=right" in r
    assert "facing=east" in r


def test_connect_fences_and_walls_row_of_three():
    # Three fences in a row along x: middle connects east+west, ends connect only inward.
    vox = {
        (0, 0, 0): "oak_fence",
        (1, 0, 0): "oak_fence",
        (2, 0, 0): "oak_fence",
    }
    connect_fences_and_walls(vox)
    assert vox[(0, 0, 0)] == "oak_fence[east=true,north=false,south=false,waterlogged=false,west=false]"
    assert vox[(1, 0, 0)] == "oak_fence[east=true,north=false,south=false,waterlogged=false,west=true]"
    assert vox[(2, 0, 0)] == "oak_fence[east=false,north=false,south=false,waterlogged=false,west=true]"


def test_connect_fences_and_walls_wall_next_to_solid():
    vox = {
        (0, 0, 0): "stone_brick_wall",
        (1, 0, 0): "stone_bricks",
    }
    connect_fences_and_walls(vox)
    out = vox[(0, 0, 0)]
    assert "east=low" in out
    assert "west=none" in out


def test_fix_stair_corners_outer_right_l_shape():
    # Hand-derived from vanilla StairsBlock.getStairsShape:
    # Stair A at (0,0,0) faces south (its low step points north, i.e. built with
    # stairs_toward(block, "n")). Its FRONT neighbour (south, +z) is stair B at
    # (0,0,1) facing west (built with stairs_toward(block, "e")).
    # facing(A)=south, facing(B)=west: in the CW cycle [north,east,south,west],
    # index(south)=2, index(west)=3 = index(south)+1 -> west is the CLOCKWISE
    # neighbour of south -> per vanilla (dirFront == dir.getCounterClockWise() ->
    # OUTER_LEFT, else OUTER_RIGHT) this is NOT the counter-clockwise case, so A
    # becomes OUTER_RIGHT.
    # Stair B's own front (west, -x) and back (east, +x) are both empty -- the
    # neighbouring stair A sits on B's *lateral* (north) side, which vanilla's
    # algorithm never inspects -- so B stays straight.
    a = stairs_toward("stone_stairs", "n")  # facing=south
    b = stairs_toward("stone_stairs", "e")  # facing=west
    vox = {
        (0, 0, 0): a,
        (0, 0, 1): b,
    }
    fix_stair_corners(vox)
    assert "shape=outer_right" in vox[(0, 0, 0)]
    assert "facing=south" in vox[(0, 0, 0)]
    assert "shape=straight" in vox[(0, 0, 1)]
    assert "facing=west" in vox[(0, 0, 1)]


def test_fix_stair_corners_no_neighbours_stays_straight():
    vox = {(0, 0, 0): stairs("stone_stairs", "north")}
    fix_stair_corners(vox)
    assert "shape=straight" in vox[(0, 0, 0)]
