#!/usr/bin/env python3
"""
Parametric CAD Generator for 1995 GMC Sonoma Full Replacement Bench Console
"Mega-Deck" Pro Edition:
  - Replaces factory blue 60/40 bench seat cupholder entirely
  - Dual 90mm-deep stepped cupholders (fits 12oz cans up to 40oz Stanleys & Yetis)
  - Dual outboard 38mm mug handle slots
  - Dedicated Milwaukee Fastback 6-in-1 (48-22-1505) vertical knife holster
  - Dedicated vertical smartphone dock (fits large phones with cases up to 88x17mm)
  - Forward catch-all cargo tray for keys, coins, AirPods, toll cards
  - Calibrated seat receiver tongue (110mm W x 95mm L x 7.5mm T)
  - Calibrated low-profile floor glide stilt / stabilizer foot for the transmission tunnel
"""

import math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection, JoinType

SEG = 96
IN = 25.4

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


def generate_1995_megadeck_console():
    """
    Full replacement bench seat console engineered for 1995 GMC Sonoma / Chevy S10:
    - Dual stepped cups (90mm depth, 3.6" top flare, 3.2" mid bore, 2.75" low pocket)
    - Dual handle cutouts
    - Dedicated Fastback holster
    - Dedicated smartphone slot
    - Catch-all tray
    - 110x95mm seat receiver tongue
    - Underside socket for calibrated stilt leg
    """
    # Coordinate system:
    # Origin (0,0,0) is centered between the two cups at the top rim surface.
    # +X: Passenger side, -X: Driver side
    # +Y: Forward (towards dash), -Y: Rearward (towards seat cushion)
    # Z=0: Top rim, -Z: Extends downward towards floor
    
    deck = Manifold()
    
    CUP_SPACING_X = 112.0
    CUP_TOP_D = 91.44      # 3.60"
    CUP_MID_D = 81.28      # 3.20"
    CUP_LOW_D = 69.85      # 2.75"
    CUP_DEPTH = 90.0
    FLARE_H = 12.0
    STEP_DEPTH = 65.0
    WALL_T = 3.6
    FLOOR_T = 4.0
    
    r_top_out = (CUP_TOP_D / 2) + WALL_T
    r_mid_out = (CUP_MID_D / 2) + WALL_T
    r_low_out = (CUP_LOW_D / 2) + WALL_T
    
    # 1. Main Outer Shell (Cups + Center Bridge + Forward Cargo Extension)
    # Forward extension reaches +Y = +68.0 mm to house phone dock & catch-all tray
    slab_h = 10.0
    outer_2d = CrossSection.circle(r_top_out, SEG).translate([-CUP_SPACING_X/2, 0]) + \
               CrossSection.circle(r_top_out, SEG).translate([CUP_SPACING_X/2, 0]) + \
               rrect(140.0, 50.0, 10.0).translate([0, 42.0])
    outer_2d = outer_2d.hull()
    
    top_slab = outer_2d.extrude(slab_h).translate([0, 0, -slab_h])
    deck += top_slab
    
    # Cup outer bodies
    for cx in (-CUP_SPACING_X/2, CUP_SPACING_X/2):
        body = cone(r_top_out*2, r_mid_out*2, -FLARE_H, 0, cx, 0)
        body += cyl(r_mid_out*2, -STEP_DEPTH, -FLARE_H, cx, 0)
        body += cone(r_mid_out*2, r_low_out*2, -STEP_DEPTH - 5.0, -STEP_DEPTH, cx, 0)
        body += cyl(r_low_out*2, -CUP_DEPTH, -STEP_DEPTH - 5.0, cx, 0)
        deck += body
        
    # Center & forward solid bridge body
    bridge_w = CUP_SPACING_X - r_low_out + 6.0
    bridge = box(-bridge_w/2, bridge_w/2, -r_top_out*0.75, 45.0, -CUP_DEPTH + 8.0, 0)
    # Forward tray body
    fwd_body = rrect(130.0, 48.0, 8.0).extrude(38.0).translate([0, 42.0, -38.0])
    deck += bridge + fwd_body
    
    # 2. Hollow Out Stepped Cup Interiors
    rf, rm, rl = CUP_TOP_D/2, CUP_MID_D/2, CUP_LOW_D/2
    for cx in (-CUP_SPACING_X/2, CUP_SPACING_X/2):
        cup_void = cone(rf*2, rm*2, -FLARE_H, 1.0, cx, 0)
        cup_void += cyl(rm*2, -STEP_DEPTH, -FLARE_H, cx, 0)
        step_h = rm - rl
        cup_void += cone(rm*2, rl*2, -STEP_DEPTH - step_h, -STEP_DEPTH, cx, 0)
        cup_void += cyl(rl*2, -CUP_DEPTH + FLOOR_T, -STEP_DEPTH - step_h, cx, 0)
        cup_void += cone(rl*2, (rl - 4.0)*2, -CUP_DEPTH + FLOOR_T - 2.0, -CUP_DEPTH + FLOOR_T, cx, 0)
        deck -= cup_void
        
    # 3. Mug Handle Cutouts (38mm wide x 50mm deep)
    HANDLE_W = 38.0
    HANDLE_D = 50.0
    # Left cup: notch facing -X
    deck -= box(-CUP_SPACING_X/2 - r_top_out - 6.0, -CUP_SPACING_X/2 + rm - 4.0, -HANDLE_W/2, HANDLE_W/2, -HANDLE_D, 5.0)
    # Right cup: notch facing +X
    deck -= box(CUP_SPACING_X/2 - rm + 4.0, CUP_SPACING_X/2 + r_top_out + 6.0, -HANDLE_W/2, HANDLE_W/2, -HANDLE_D, 5.0)
    
    # 4. Dedicated Milwaukee Fastback 6-in-1 (48-22-1505) Holster
    # Centered between cups at Y = -8.0 mm
    # Fastback closed: 38mm wide x 21mm thick. Holster: 40.5mm x 23.0mm x 55mm deep.
    fastback_void = rrect(40.5, 23.0, 3.5).extrude(55.0).translate([0, -8.0, -55.0])
    # Pocket clip clearance channel on front edge
    clip_relief = box(-12.0, 12.0, 1.0, 6.0, -38.0, 2.0)
    deck -= (fastback_void + clip_relief)
    
    # 5. Dedicated Smartphone / Battery Bank Dock
    # Positioned forward at Y = +25.0 mm, Width 88.0mm, Thickness 16.5mm, Depth 35.0mm
    phone_void = rrect(88.0, 16.5, 4.0).extrude(35.0).translate([0, 24.0, -35.0])
    deck -= phone_void
    
    # 6. Forward Catch-All Cargo Tray
    # Positioned at Y = +52.0 mm, Width 94.0mm, Length 26.0mm, Depth 22.0mm
    tray_void = rrect(94.0, 26.0, 5.0).extrude(22.0).translate([0, 52.0, -22.0])
    deck -= tray_void
    
    # 7. Seat Receiver Mounting Tongue (extending -Y into seat frame)
    # Calibrated to 1995 Sonoma bench receiver:
    # In truck photos, receiver bracket slot sits ~55mm below cupholder top rim
    TONGUE_W = 110.0
    TONGUE_L = 95.0
    TONGUE_T = 7.5
    tongue_start_y = -r_top_out * 0.60
    tongue_end_y = tongue_start_y - TONGUE_L
    tongue_z_top = -52.0
    tongue_z_bot = tongue_z_top - TONGUE_T
    
    tongue = rrect(TONGUE_W, TONGUE_L, 6.0).extrude(TONGUE_T).translate([0, tongue_start_y - TONGUE_L/2, tongue_z_bot])
    # Retention catch bump
    catch = rrect(20.0, 12.0, 3.0).extrude(2.5).translate([0, tongue_end_y + 20.0, tongue_z_top - 0.1])
    # Reinforced gusset connecting tongue to cupholder rear body
    gusset = box(-TONGUE_W/2 + 4.0, TONGUE_W/2 - 4.0, tongue_start_y - 25.0, tongue_start_y + 6.0, tongue_z_bot - 8.0, 0)
    
    deck += tongue + catch + gusset
    
    # Clean cup bores again in case gusset overlapped
    for cx in (-CUP_SPACING_X/2, CUP_SPACING_X/2):
        deck -= cyl(rm*2, -STEP_DEPTH, 2.0, cx, 0)
        deck -= cyl(rl*2, -CUP_DEPTH + FLOOR_T, -STEP_DEPTH, cx, 0)
        
    # 8. Underside Mortise Socket for Stabilizer Stilt Leg
    # Socket centered under the bridge at Z = -CUP_DEPTH + 8.0
    SOCKET_W = 36.0
    SOCKET_L = 46.0
    SOCKET_D = 22.0
    socket_bot = -CUP_DEPTH + 6.0
    socket_void = rrect(SOCKET_W, SOCKET_L, 3.0).extrude(SOCKET_D + 2.0).translate([0, 5.0, socket_bot - 0.5])
    deck -= socket_void
    
    return deck


def generate_1995_calibrated_stilt():
    """
    Calibrated low-profile floor stabilizer stilt leg for the 1995 Mega-Deck:
    - Matches underside socket (35.5mm x 45.5mm tenon)
    - Reaches from cup bottom (-90mm) down to transmission hump (drop ~26mm)
    - Total stilt body height = 26.0mm + 21mm tenon
    - 300mm curved transmission tunnel glide foot with 38mm felt pad recess
    """
    SOCKET_W = 36.0
    SOCKET_L = 46.0
    TENON_H = 21.0
    TOL = 0.25
    
    tenon_w = SOCKET_W - 2*TOL
    tenon_l = SOCKET_L - 2*TOL
    tenon = rrect(tenon_w, tenon_l, 3.2).extrude(TENON_H).translate([0, 5.0, 0])
    
    # Stilt drop below deck bottom
    DROP_H = 26.0
    FOOT_W = 85.0
    FOOT_L = 60.0
    
    collar = rrect(tenon_w + 10.0, tenon_l + 10.0, 4.0).extrude(8.0).translate([0, 5.0, -8.0])
    foot = rrect(FOOT_W, FOOT_L, 8.0).extrude(DROP_H - 8.0).translate([0, 5.0, -DROP_H])
    
    # 300mm curved transmission hump arc
    R_CURVE = 300.0
    curve_cyl = cyl(R_CURVE*2, -FOOT_L/2 - 10.0, FOOT_L/2 + 20.0, 0, 5.0).rotate([90, 0, 0]).translate([0, 0, -DROP_H - R_CURVE + 3.0])
    felt_pocket = cyl(38.0, -DROP_H - 1.0, -DROP_H + 2.0, 0, 5.0)
    
    stilt = (tenon + collar + foot) - curve_cyl - felt_pocket
    return stilt


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cupholder_dir = os.path.join(base_dir, "stls", "cupholder")
    os.makedirs(cupholder_dir, exist_ok=True)
    
    print("Generating 1995 Sonoma Mega-Deck Console...")
    megadeck = generate_1995_megadeck_console()
    to_tm(megadeck).export(os.path.join(cupholder_dir, "sonoma_cupholder_1995_megadeck.stl"))
    print("  -> sonoma_cupholder_1995_megadeck.stl")
    
    print("Generating 1995 Sonoma Calibrated Stilt...")
    stilt = generate_1995_calibrated_stilt()
    to_tm(stilt).export(os.path.join(cupholder_dir, "sonoma_cupholder_1995_stilt_26mm.stl"))
    print("  -> sonoma_cupholder_1995_stilt_26mm.stl")

if __name__ == "__main__":
    main()
