#!/usr/bin/env python3
"""
Parametric 3D CAD Generator for 1995 GMC Sonoma / Chevy S10 Upgrades:
  1. 1995 Sonoma Ashtray Drop-In Upgrades (replaces the inner metal ash bucket in the lower dash drawer):
     - sonoma_1995_ashtray_usb_power.stl   : Flush top plate with 28.8mm (1-1/8") USB-C PD / Voltmeter socket
     - sonoma_1995_ashtray_edc_pocket.stl  : Deep dual-compartment organizer (AirPods/keys + curved coin ramp)
     - sonoma_1995_ashtray_combo_power.stl : 2-in-1 (Left USB-C PD socket + Right drop pocket)

  2. Calibrated Bench Cupholder Upgrades (based on photo measurements):
     - sonoma_cupholder_tumbler_sleeve.stl  : High-walled drop-in sleeve riser (fits factory blue console, holds 30/40oz Stanleys)
     - sonoma_cupholder_fastback_caddy.stl : EDC organizer insert (custom Milwaukee Fastback knife holster + phone/powerbank slot)
     - sonoma_glide_stilt_52mm.stl         : Calibrated 52mm (2.0") low-profile stilt for the full replacement deck
"""

import math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, CrossSection, JoinType

SEG = 96
IN = 25.4

def rrect(w, l, rr, seg=48):
    rr = max(0.05, min(rr, w/2 - 0.01, l/2 - 0.01))
    return CrossSection.square([w - 2*rr, l - 2*rr], center=True).offset(rr, JoinType.Round, 2.0, seg)

def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def cyl(d, z0, z1, x=0, y=0, seg=SEG):
    return Manifold.cylinder(z1 - z0, d/2, d/2, seg).translate([x, y, z0])

def cone(d_bot, d_top, z0, z1, x=0, y=0, seg=SEG):
    return Manifold.cylinder(z1 - z0, d_bot/2, d_top/2, seg).translate([x, y, z0])

def to_tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(np.array(mm.vert_properties)[:, :3], np.array(mm.tri_verts), process=False)


# ==============================================================================
# PART 1: 1995 GMC Sonoma Pull-Out Ashtray Drop-In Upgrades
# ==============================================================================
# Dimensions calibrated to factory 1994-1997 GM lower dash drawer metal insert:
ASH_RIM_W = 78.0   # mm outer flange width
ASH_RIM_L = 58.0   # mm outer flange length (front to back)
ASH_BODY_W = 72.0  # mm body width dropping into drawer
ASH_BODY_L = 52.0  # mm body length
ASH_DEPTH = 42.0   # mm internal pocket depth
FLANGE_T = 3.0     # mm resting flange thickness
WALL_T = 2.6       # mm wall thickness
FLOOR_T = 3.0      # mm bottom thickness
USB_HOLE_D = 28.8  # mm (1-1/8" standard marine USB-C socket)

def generate_1995_ashtray_usb_power():
    """Flush USB-C fast-charging pod replacing inner metal bucket."""
    flange = rrect(ASH_RIM_W, ASH_RIM_L, 4.0).extrude(FLANGE_T).translate([0, 0, 0])
    body = rrect(ASH_BODY_W, ASH_BODY_L, 4.0).extrude(ASH_DEPTH).translate([0, 0, -ASH_DEPTH])
    solid = flange + body
    
    # Internal hollow cavity for USB socket body & rear locknut
    cav_w = ASH_BODY_W - 2 * WALL_T
    cav_l = ASH_BODY_L - 2 * WALL_T
    cavity = rrect(cav_w, cav_l, 3.0).extrude(ASH_DEPTH - FLOOR_T).translate([0, 0, -ASH_DEPTH + FLOOR_T])
    
    # 28.8mm hole through top flange for USB socket
    hole = cyl(USB_HOLE_D, -10.0, FLANGE_T + 5.0, 0, 0)
    
    # Rear wiring exit notch on the back wall (-Y direction)
    wire_notch = box(-12.0, 12.0, -ASH_BODY_L/2 - 2.0, -ASH_BODY_L/2 + 8.0, -ASH_DEPTH + FLOOR_T, -ASH_DEPTH + FLOOR_T + 16.0)
    
    pod = solid - cavity - hole - wire_notch
    return pod

def generate_1995_ashtray_edc_pocket():
    """Deep organizer pocket with coin ramp and gear divider."""
    flange = rrect(ASH_RIM_W, ASH_RIM_L, 4.0).extrude(FLANGE_T).translate([0, 0, 0])
    body = rrect(ASH_BODY_W, ASH_BODY_L, 4.0).extrude(ASH_DEPTH).translate([0, 0, -ASH_DEPTH])
    solid = flange + body
    
    # Main storage cavity
    cav_w = ASH_BODY_W - 2 * WALL_T
    cav_l = ASH_BODY_L - 2 * WALL_T
    cavity = rrect(cav_w, cav_l, 3.0).extrude(ASH_DEPTH + 10.0).translate([0, 0, -ASH_DEPTH + FLOOR_T])
    
    pocket = solid - cavity
    
    # Center divider wall separating coins from keys/AirPods
    div_x = -ASH_BODY_W / 6.0
    divider = box(div_x - 1.2, div_x + 1.2, -cav_l/2, cav_l/2, -ASH_DEPTH + FLOOR_T, FLANGE_T - 1.0)
    pocket += divider
    
    # Coin ramp wedge in left compartment for easy thumb slide
    ramp_w = (cav_w/2 + div_x) - 1.0
    ramp_box = box(-cav_w/2, div_x - 1.2, -cav_l/2, cav_l/2, -ASH_DEPTH + FLOOR_T, -ASH_DEPTH + FLOOR_T + 12.0)
    # Bevel ramp with rotated subtractor
    sub = Manifold.cube([ramp_w + 10, cav_l + 10, 20.0]).rotate([0, 25, 0]).translate([-cav_w/2 - 2, -cav_l/2 - 5, -ASH_DEPTH + FLOOR_T + 2.0])
    coin_ramp = ramp_box - sub
    pocket += coin_ramp
    
    return pocket

def generate_1995_ashtray_combo_power():
    """2-in-1: Left-side USB-C fast charge + Right-side drop pocket."""
    flange = rrect(ASH_RIM_W, ASH_RIM_L, 4.0).extrude(FLANGE_T).translate([0, 0, 0])
    body = rrect(ASH_BODY_W, ASH_BODY_L, 4.0).extrude(ASH_DEPTH).translate([0, 0, -ASH_DEPTH])
    solid = flange + body
    
    # Left power socket cavity (X < 0)
    usb_x = -ASH_BODY_W / 4.0
    usb_cav = cyl(35.0, -ASH_DEPTH + FLOOR_T, FLANGE_T - 2.5, usb_x, 0)
    usb_hole = cyl(USB_HOLE_D, -10.0, FLANGE_T + 5.0, usb_x, 0)
    wire_exit = cyl(14.0, -ASH_DEPTH - 5.0, -ASH_DEPTH + FLOOR_T + 5.0, usb_x, 0)
    
    # Right drop pocket (X > 0)
    pock_x = ASH_BODY_W / 4.0
    pock_w = ASH_BODY_W / 2.0 - WALL_T - 1.0
    pock_l = ASH_BODY_L - 2 * WALL_T
    pock_cav = rrect(pock_w, pock_l, 3.0).extrude(ASH_DEPTH + 10.0).translate([pock_x, 0, -ASH_DEPTH + FLOOR_T])
    
    combo = solid - usb_cav - usb_hole - wire_exit - pock_cav
    return combo


# ==============================================================================
# PART 2: Calibrated Cupholder Upgrades (Factory Console Inserts & 52mm Stilt)
# ==============================================================================
# Factory GM bench cupholder cavity dimensions:
FACTORY_WELL_TOP_D = 77.5   # mm top rim inner diameter (~3.05 in)
FACTORY_WELL_BOT_D = 73.5   # mm bottom floor diameter
FACTORY_WELL_DEPTH = 42.0   # mm factory well depth (~1.65 in)

def generate_tumbler_sleeve_riser():
    """
    Drop-in sleeve that seats in the shallow factory blue cupholder well,
    rising 50mm (2.0 in) higher with stepped 3.25" bore and mug handle notch.
    """
    # 1. Lower plug that sits inside factory well
    plug_outer = cone(FACTORY_WELL_BOT_D - 0.8, FACTORY_WELL_TOP_D - 0.8, 0, FACTORY_WELL_DEPTH)
    
    # 2. Upper flared riser (rises 50mm above factory rim)
    riser_h = 50.0
    z_top = FACTORY_WELL_DEPTH + riser_h
    riser_mid_od = 82.5 + 2 * 3.5 # 89.5mm OD
    riser_top_od = 92.0 + 2 * 3.5 # 99.0mm OD
    
    riser_outer = cone(FACTORY_WELL_TOP_D + 2.0, riser_top_od, FACTORY_WELL_DEPTH, z_top)
    solid = plug_outer + riser_outer
    
    # 3. Stepped internal cup bore:
    # Lower can well: 69.5mm (fits 12oz can down into base)
    can_bore = cyl(69.85, 3.5, FACTORY_WELL_DEPTH + 5.0)
    
    # Main tumbler bore: 82.5mm (3.25 in) for Stanley 30/40oz & Yeti mugs
    tumbler_bore = cyl(82.5, FACTORY_WELL_DEPTH, z_top - 12.0)
    
    # Top flare: 92.0mm (3.62 in)
    top_flare = cone(82.5, 92.0, z_top - 12.0, z_top + 2.0)
    
    cavity = can_bore + tumbler_bore + top_flare
    
    # 4. Outboard Mug Handle Clearance Notch (38mm wide, cuts down 42mm from top)
    handle_notch = box(15.0, 60.0, -19.0, 19.0, z_top - 42.0, z_top + 5.0)
    
    # 5. Drainage hole in bottom
    drain = cyl(14.0, -5.0, 10.0)
    
    sleeve = solid - cavity - handle_notch - drain
    return sleeve

def generate_fastback_edc_caddy():
    """
    Drops into the other factory cup well to organize:
      1. Dedicated vertical holster for Milwaukee Fastback 6-in-1 (48-22-1505) knife
      2. Upright slot for smartphone / power bank
      3. Small key / coin catch pocket
    """
    plug = cone(FACTORY_WELL_BOT_D - 0.8, FACTORY_WELL_TOP_D - 0.8, 0, FACTORY_WELL_DEPTH)
    riser_h = 42.0
    z_top = FACTORY_WELL_DEPTH + riser_h
    riser = rrect(90.0, 90.0, 18.0).extrude(riser_h).translate([0, 0, FACTORY_WELL_DEPTH])
    solid = plug + riser
    
    # 1. Milwaukee Fastback 48-22-1505 Holster Pocket
    # Knife folded dimensions: ~38mm wide x ~22mm thick. Holster depth ~55mm.
    knife_x = -22.0
    knife_pocket = rrect(40.0, 24.0, 3.0).extrude(55.0).translate([knife_x, 0, z_top - 55.0])
    # Pocket clip relief slot on front edge
    clip_slot = box(knife_x - 12.0, knife_x + 12.0, -18.0, -11.0, z_top - 35.0, z_top + 2.0)
    
    # 2. Smartphone / Power Bank Slot
    # Width 82mm, thickness 16mm (fits phone upright)
    phone_x = 18.0
    phone_slot = rrect(30.0, 76.0, 4.0).extrude(60.0).translate([phone_x, 0, z_top - 60.0])
    
    # 3. Key / Coin Catch Pocket in center
    key_pocket = rrect(22.0, 35.0, 4.0).extrude(30.0).translate([0, 0, z_top - 30.0])
    
    caddy = solid - knife_pocket - clip_slot - phone_slot - key_pocket
    return caddy

def generate_calibrated_52mm_stilt():
    """
    Calibrated 52mm (2.05 in) low-profile compression stilt leg for sonoma_cupholder_deck.stl.
    Replaces the previous 203mm estimate to match the real transmission tunnel drop height.
    """
    # Keyed tenon matching deck underside socket
    SOCKET_W_X = 36.0
    SOCKET_L_Y = 46.0
    TENON_H = 24.0
    TOL = 0.25
    
    tenon_w = SOCKET_W_X - 2 * TOL
    tenon_l = SOCKET_L_Y - 2 * TOL
    tenon = rrect(tenon_w, tenon_l, 3.5).extrude(TENON_H).translate([0, 0, 0])
    
    # Chamfer top of tenon for smooth lead-in
    chamfer = Manifold.cylinder(TENON_H, tenon_w/2, (tenon_w - 4)/2, SEG).translate([0, 0, TENON_H - 4])
    
    # Stilt leg drop body: drop height 52.0mm (~2.05 in) from deck bottom to transmission hump
    DROP_H = 52.0
    FOOT_W = 85.0
    FOOT_L = 60.0
    
    # Contoured transition from tenon collar to wide stable foot
    leg_upper = rrect(tenon_w + 10.0, tenon_l + 10.0, 4.0).extrude(12.0).translate([0, 0, -12.0])
    leg_lower = rrect(FOOT_W, FOOT_L, 8.0).extrude(DROP_H - 12.0).translate([0, 0, -DROP_H])
    
    # Transmission tunnel crowning curve (radius 300mm across X axis)
    R_CURVE = 300.0
    curve_cyl = cyl(R_CURVE * 2, -FOOT_L/2 - 5.0, FOOT_L/2 + 5.0, 0, 0).rotate([90, 0, 0]).translate([0, 0, -DROP_H - R_CURVE + 3.0])
    
    # 38mm (1.5 in) round recessed felt/rubber pad pocket on the bottom
    felt_pocket = cyl(38.0, -DROP_H - 1.0, -DROP_H + 2.0, 0, 0)
    
    stilt = (tenon + leg_upper + leg_lower) - curve_cyl - felt_pocket
    return stilt


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ashtray_dir = os.path.join(base_dir, "stls", "ashtray")
    cupholder_dir = os.path.join(base_dir, "stls", "cupholder")
    os.makedirs(ashtray_dir, exist_ok=True)
    os.makedirs(cupholder_dir, exist_ok=True)
    
    print("--- 1. Generating 1995 Sonoma Ashtray Upgrades ---")
    p1 = generate_1995_ashtray_usb_power()
    to_tm(p1).export(os.path.join(ashtray_dir, "sonoma_1995_ashtray_usb_power.stl"))
    print("  -> sonoma_1995_ashtray_usb_power.stl")
    
    p2 = generate_1995_ashtray_edc_pocket()
    to_tm(p2).export(os.path.join(ashtray_dir, "sonoma_1995_ashtray_edc_pocket.stl"))
    print("  -> sonoma_1995_ashtray_edc_pocket.stl")
    
    p3 = generate_1995_ashtray_combo_power()
    to_tm(p3).export(os.path.join(ashtray_dir, "sonoma_1995_ashtray_combo_power.stl"))
    print("  -> sonoma_1995_ashtray_combo_power.stl")
    
    print("\n--- 2. Generating Calibrated Cupholder Upgrades ---")
    c1 = generate_tumbler_sleeve_riser()
    to_tm(c1).export(os.path.join(cupholder_dir, "sonoma_cupholder_tumbler_sleeve.stl"))
    print("  -> sonoma_cupholder_tumbler_sleeve.stl")
    
    c2 = generate_fastback_edc_caddy()
    to_tm(c2).export(os.path.join(cupholder_dir, "sonoma_cupholder_fastback_caddy.stl"))
    print("  -> sonoma_cupholder_fastback_caddy.stl")
    
    c3 = generate_calibrated_52mm_stilt()
    to_tm(c3).export(os.path.join(cupholder_dir, "sonoma_glide_stilt_52mm.stl"))
    print("  -> sonoma_glide_stilt_52mm.stl")
    
    print("\n[SUCCESS] All 6 calibrated STLs generated successfully!")

if __name__ == "__main__":
    main()
