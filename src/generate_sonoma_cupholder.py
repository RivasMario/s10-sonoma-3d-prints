#!/usr/bin/env python3
"""
Parametric 3D CAD generator for 1994-2004 GMC Sonoma / Chevy S10 Bench Seat Cupholder
Two-part modular assembly:
  1. sonoma_cupholder_deck.stl - Side-by-side dual stepped cups, handle notches, seat tongue, socket
  2. sonoma_glide_stilt.stl   - Ribbed compression stilt leg with keyed tenon & curved glide foot
"""
import math, sys, os
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection, JoinType

IN = 25.4

# ----------------- Configuration & Dimensions -----------------
# Seat slot tongue (matches GM S10 factory bench receiver slot)
TONGUE_W = 110.0          # mm (~4.33 in)
TONGUE_L = 95.0           # mm into seat slot (~3.74 in)
TONGUE_T = 7.5            # mm slot thickness
TONGUE_CATCH_H = 2.5      # latch bump height
TONGUE_CATCH_W = 20.0
TONGUE_CATCH_L = 12.0

# Cupholders (Side-by-Side)
CUP_SPACING_X = 108.0     # center-to-center distance between cups
CUP_TOP_D   = 3.60 * IN   # 91.44 mm: top flare opening (32/40oz wide bottles)
CUP_MID_D   = 3.20 * IN   # 81.28 mm: main bore (Stanley 30/40, YETI 35 straw mug)
CUP_LOW_D   = 2.75 * IN   # 69.85 mm: lower can pocket (12oz cans, standard bottles)
CUP_DEPTH   = 90.0        # mm (~3.54 in total depth)
FLARE_H     = 12.0        # top flare height
STEP_DEPTH  = 65.0        # depth down to mid->low step
LOW_POCKET_H = 20.0       # height of lowest 2.75" pocket
WALL_T      = 4.0         # wall thickness
FLOOR_T     = 4.5         # bottom floor thickness

# Mug handle cutouts (outboard: left notch on driver cup, right notch on pass cup)
HANDLE_W    = 38.0        # 1.5 in width
HANDLE_D    = 52.0        # cut down from top rim

# Stilt socket & tenon
SOCKET_W_X  = 36.0        # mm width
SOCKET_L_Y  = 46.0        # mm length
SOCKET_DEPTH = 25.0       # mm depth into deck underside
TOLERANCE   = 0.25        # per-side clearance for snug press fit

# Stilt leg
TOTAL_DROP_H = 8.0 * IN   # 203.2 mm (nominal 8.0 inches from seat bottom to transmission hump)
FOOT_W_X    = 85.0        # mm foot width
FOOT_L_Y    = 60.0        # mm foot length
FOOT_R_CURVE = 300.0      # hump crowning curvature radius
FELT_PAD_D  = 38.0        # 1.5 in round felt pad recess

SEG = 96

# ----------------- Helper functions -----------------
def rrect(w, l, rr, seg=48):
    rr = max(0.05, min(rr, w/2 - 0.01, l/2 - 0.01))
    return CrossSection.square([w - 2*rr, l - 2*rr], center=True).offset(rr, JoinType.Round, 2.0, seg)

def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def cyl(d, z0, z1, x=0, y=0, seg=SEG):
    return Manifold.cylinder(z1 - z0, d/2, d/2, seg).translate([x, y, z0])

def cone(d0, d1, z0, z1, x=0, y=0, seg=SEG):
    return Manifold.cylinder(z1 - z0, d0/2, d1/2, seg).translate([x, y, z0])

def to_tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(np.array(mm.vert_properties)[:, :3], np.array(mm.tri_verts), process=False)

# ----------------- Part 1: Cupholder Deck -----------------
def generate_cupholder_deck():
    # Coordinate system:
    # Origin (0,0,0) is centered horizontally between the two cups at the top deck surface.
    # +X is Passenger side (Right), -X is Driver side (Left).
    # +Y is Forward (towards dash), -Y is Rear (towards seat cushion).
    # Z=0 is the top rim surface of the cups, -Z extends downwards.
    
    deck = Manifold()
    
    # 1. Outer perimeter hull of the two cup housings + center bridge
    # Left cup center = -CUP_SPACING_X / 2, Right cup center = +CUP_SPACING_X / 2
    r_out = (CUP_TOP_D / 2) + WALL_T
    
    # Rounded deck slab at top
    deck_slab_h = 10.0
    deck_2d = CrossSection.circle(r_out, SEG).translate([-CUP_SPACING_X/2, 0]) + \
              CrossSection.circle(r_out, SEG).translate([CUP_SPACING_X/2, 0])
    deck_2d = deck_2d.hull()
    
    # Extrude outer deck
    deck_top = deck_2d.extrude(deck_slab_h).translate([0, 0, -deck_slab_h])
    
    # Cup body outer cylinders/cones tapering down
    r_mid_out = (CUP_MID_D / 2) + WALL_T
    r_low_out = (CUP_LOW_D / 2) + WALL_T
    
    for cx in (-CUP_SPACING_X/2, CUP_SPACING_X/2):
        # Upper section
        cup_body = cone(r_out*2, r_mid_out*2, -FLARE_H, 0, cx, 0)
        # Mid bore body
        cup_body += cyl(r_mid_out*2, -STEP_DEPTH, -FLARE_H, cx, 0)
        # Low pocket body
        cup_body += cone(r_mid_out*2, r_low_out*2, -STEP_DEPTH - 5.0, -STEP_DEPTH, cx, 0)
        cup_body += cyl(r_low_out*2, -CUP_DEPTH, -STEP_DEPTH - 5.0, cx, 0)
        deck += cup_body

    # Bridge between cups (thick solid web to house the socket underneath)
    bridge_w = CUP_SPACING_X - r_low_out
    bridge = box(-bridge_w/2, bridge_w/2, -r_out * 0.75, r_out * 0.75, -CUP_DEPTH + 5.0, 0)
    deck += bridge
    deck += deck_top
    
    # 2. Hollow out the stepped cup interiors
    rf, rm, rl = CUP_TOP_D/2, CUP_MID_D/2, CUP_LOW_D/2
    for cx in (-CUP_SPACING_X/2, CUP_SPACING_X/2):
        # Top flare
        cup_void = cone(rf*2, rm*2, -FLARE_H, 1.0, cx, 0)
        # Mid bore
        cup_void += cyl(rm*2, -STEP_DEPTH, -FLARE_H, cx, 0)
        # 45 deg step transition to low pocket
        step_h = rm - rl
        cup_void += cone(rm*2, rl*2, -STEP_DEPTH - step_h, -STEP_DEPTH, cx, 0)
        # Low pocket
        cup_void += cyl(rl*2, -CUP_DEPTH + FLOOR_T, -STEP_DEPTH - step_h, cx, 0)
        # Closed beveled floor
        cup_void += cone(rl*2, (rl - 4.0)*2, -CUP_DEPTH + FLOOR_T - 2.0, -CUP_DEPTH + FLOOR_T, cx, 0)
        deck -= cup_void
        
    # 3. Mug handle cutouts (Outboard)
    # Left cup: notch facing -X
    deck -= box(-CUP_SPACING_X/2 - r_out - 5.0, -CUP_SPACING_X/2 + rm - 4.0, -HANDLE_W/2, HANDLE_W/2, -HANDLE_D, 5.0)
    # Right cup: notch facing +X
    deck -= box(CUP_SPACING_X/2 - rm + 4.0, CUP_SPACING_X/2 + r_out + 5.0, -HANDLE_W/2, HANDLE_W/2, -HANDLE_D, 5.0)
    
    # 4. Small utility pocket / key tray in center between cups
    pocket_w, pocket_l, pocket_d = 26.0, 50.0, 18.0
    deck -= rrect(pocket_w, pocket_l, 4.0).extrude(pocket_d).translate([0, 0, -pocket_d])

    # 5. Seat Slot Mounting Tongue (extending -Y towards seat)
    # Tongue extends from rear of deck back by TONGUE_L
    tongue_start_y = -r_out * 0.60
    tongue_end_y = tongue_start_y - TONGUE_L
    # Tongue sits at height corresponding to center of seat slot
    tongue_z_top = -deck_slab_h
    tongue_z_bot = tongue_z_top - TONGUE_T
    
    tongue = rrect(TONGUE_W, TONGUE_L, 6.0).extrude(TONGUE_T).translate([0, tongue_start_y - TONGUE_L/2, tongue_z_bot])
    
    # Gusset / reinforcement transition between tongue and cups
    gusset = box(-TONGUE_W/2 + 5.0, TONGUE_W/2 - 5.0, tongue_start_y - 25.0, tongue_start_y + 10.0, -CUP_DEPTH + 15.0, tongue_z_top)
    # Bevel the gusset with a batch hull or angled cut
    gusset = gusset ^ box(-TONGUE_W/2, TONGUE_W/2, -200, 200, -200, 200)
    deck += tongue
    deck += gusset
    
    # Retention latch bump on top of tongue
    catch = rrect(TONGUE_CATCH_W, TONGUE_CATCH_L, 3.0).extrude(TONGUE_CATCH_H).translate([0, tongue_end_y + 20.0, tongue_z_top - 0.1])
    deck += catch
    
    # Re-clean cup bores in case tongue/gusset protruded into cup voids
    for cx in (-CUP_SPACING_X/2, CUP_SPACING_X/2):
        deck -= cyl(rm*2, -STEP_DEPTH, 2.0, cx, 0)
        deck -= cyl(rl*2, -CUP_DEPTH + FLOOR_T, -STEP_DEPTH, cx, 0)

    # 6. Underside Mortise Socket for Stilt Leg
    # Centered at (0, 0) underneath the center web
    socket_bot = -CUP_DEPTH + 5.0
    socket_void = rrect(SOCKET_W_X, SOCKET_L_Y, 3.0).extrude(SOCKET_DEPTH + 2.0).translate([0, 0, socket_bot - 0.5])
    deck -= socket_void
    
    return deck


# ----------------- Part 2: Glide Stilt Leg -----------------
def generate_stilt_leg(total_drop_mm=TOTAL_DROP_H):
    # Stilt leg connects into the socket of the deck and reaches down to the floor hump.
    # Total vertical drop from deck bottom to transmission hump.
    # Z=0 is the contact surface of the deck bottom where the stilt shoulder rests.
    # +Z is the tenon that inserts into the deck socket.
    # -Z extends downwards to the transmission hump.
    
    stilt = Manifold()
    
    # 1. Tenon (inserts 24mm into the deck socket)
    tenon_w = SOCKET_W_X - 2*TOLERANCE
    tenon_l = SOCKET_L_Y - 2*TOLERANCE
    tenon_h = SOCKET_DEPTH - 1.0
    tenon = rrect(tenon_w, tenon_l, 2.5).extrude(tenon_h).translate([0, 0, 0])
    # Lead-in chamfer at tenon top
    tenon_tip = rrect(tenon_w - 2.0, tenon_l - 2.0, 2.0).extrude(2.0).translate([0, 0, tenon_h - 1.9])
    stilt += tenon
    
    # 2. Shoulder collar (stops flush against deck underside)
    collar_h = 6.0
    collar = rrect(SOCKET_W_X + 10.0, SOCKET_L_Y + 10.0, 5.0).extrude(collar_h).translate([0, 0, -collar_h])
    stilt += collar
    
    # 3. Main Strut Column (Tapered I-beam style for massive compression stiffness)
    strut_h = total_drop_mm - collar_h - 12.0 # leaving room for foot
    top_w, top_l = SOCKET_W_X + 6.0, SOCKET_L_Y + 4.0
    bot_w, bot_l = FOOT_W_X * 0.70, FOOT_L_Y * 0.75
    
    # Hull from top collar to foot base
    strut_top = rrect(top_w, top_l, 4.0).extrude(0.1).translate([0, 0, -collar_h])
    strut_bot = rrect(bot_w, bot_l, 6.0).extrude(0.1).translate([0, 0, -collar_h - strut_h])
    strut = Manifold.batch_hull([strut_top, strut_bot])
    
    # Weight reduction / ribbing cutouts through the front and back faces (like KeyShot render)
    cutout_w = 16.0
    for cz in np.linspace(-collar_h - 25.0, -collar_h - strut_h + 25.0, 3):
        cutout = rrect(cutout_w, 20.0, 4.0).extrude(100.0).rotate([90, 0, 0]).translate([0, 50.0, cz])
        strut -= cutout
        
    stilt += strut
    
    # 4. Broad Curved Foot for Transmission Tunnel
    foot_z_top = -collar_h - strut_h
    foot_slab_h = 14.0
    foot_slab = rrect(FOOT_W_X, FOOT_L_Y, 8.0).extrude(foot_slab_h).translate([0, 0, foot_z_top - foot_slab_h])
    
    # Hollow underside with curvature matching hump
    # Curvature along X axis
    curve_cutter = Manifold.cylinder(FOOT_L_Y + 20.0, FOOT_R_CURVE, FOOT_R_CURVE, 128).rotate([90, 0, 0]).translate([0, (FOOT_L_Y+20)/2, foot_z_top - foot_slab_h - FOOT_R_CURVE + 3.0])
    foot = foot_slab - curve_cutter
    
    # Recess for stick-on felt pad (40mm x 30mm x 1.2mm deep)
    felt_void = rrect(42.0, 32.0, 4.0).extrude(1.5).translate([0, 0, foot_z_top - foot_slab_h - 0.2])
    foot -= felt_void
    
    stilt += foot
    
    return stilt


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    print("Generating Sonoma Bench Cupholder 3D Models...")
    
    # 1. Cupholder Deck
    print("Building Cupholder Deck...")
    deck = generate_cupholder_deck()
    tm_deck = to_tm(deck)
    assert tm_deck.is_watertight, "Cupholder deck mesh is not watertight!"
    # Orient for 3D printing: flat on top rim (Z flipped) or normal
    deck_path = os.path.join(out_dir, "sonoma_cupholder_deck.stl")
    tm_deck.export(deck_path)
    e = tm_deck.extents / IN
    print(f"  [OK] Deck STL: {e[0]:.2f}W x {e[1]:.2f}L x {e[2]:.2f}H inches | Volume: {deck.volume()/16387.064:.1f} in3")
    
    # 2. Stilt Leg
    print("Building Stilt Leg...")
    stilt = generate_stilt_leg(TOTAL_DROP_H)
    tm_stilt = to_tm(stilt)
    assert tm_stilt.is_watertight, "Stilt leg mesh is not watertight!"
    # Orient stilt upright on its foot
    tm_stilt.apply_translation(-tm_stilt.bounds[0])
    stilt_path = os.path.join(out_dir, "sonoma_glide_stilt.stl")
    tm_stilt.export(stilt_path)
    es = tm_stilt.extents / IN
    print(f"  [OK] Stilt STL: {es[0]:.2f}W x {es[1]:.2f}L x {es[2]:.2f}H inches | Volume: {stilt.volume()/16387.064:.1f} in3")
    
    print("\nGeneration Complete! Files saved to:", out_dir)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    main(out)
