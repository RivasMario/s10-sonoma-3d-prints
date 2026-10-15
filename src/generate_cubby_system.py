#!/usr/bin/env python3
"""
Parametric 3D CAD Generator for 1994-2004 Chevy S10 / GMC Sonoma
Modular Dash Cubby & Phone Mount System:
  1. S10_cubby_magnetic_dock.stl         - Deep storage cubby with 4x neodymium magnet corner pockets & rear cable port
  2. S10_cubby_mag_stealth_cover.stl     - Flush OEM-style stealth cover plate with matching magnet pockets & finger lift
  3. S10_cubby_mag_magsafe_plate.stl     - Magnetic snap-on 56mm MagSafe charging plate tilted 15° toward driver
  4. S10_cubby_mag_ball_plate.stl        - Magnetic snap-on 17mm ball mount plate
  5. S10_cubby_slide_dock.stl            - Cubby with internal slide tracks for push-in cartridge & open lower tray
  6. S10_slide_phone_mount.stl           - Push-in cartridge module with 17mm ball stud
  7. S10_cubby_integrated_phone_dock.stl - Monolithic 2-in-1: drop-in phone cradle + lower sunglasses cubby
"""

import math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, CrossSection, JoinType

IN = 25.4
SEG = 96

# Factory Opening Dimensions
CUBBY_W = 57.6   # mm total width
CUBBY_H = 42.2   # mm total height
WALL_T  = 3.0    # mm wall thickness
FLOOR_T = 3.5    # mm floor thickness
DEPTH   = 140.0  # mm cavity depth into dash (Deep Glasses Spec: 136.5mm internal cavity fits full folded sunglasses while clearing rear dash ductwork)

# 6mm x 3mm Round Neodymium Magnet Pockets (with 0.2mm press-fit tolerance)
MAG_D = 6.3      # mm pocket diameter
MAG_DEPTH = 3.2  # mm pocket depth
MAG_X = 23.0     # +/- mm from center
MAG_Y = 15.5     # +/- mm from center

def rrect(w, l, rr, seg=48):
    rr = max(0.05, min(rr, w/2 - 0.01, l/2 - 0.01))
    return CrossSection.square([w - 2*rr, l - 2*rr], center=True).offset(rr, JoinType.Round, 2.0, seg)

def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def cyl(d, z0, z1, x=0, y=0, seg=SEG):
    return Manifold.cylinder(z1 - z0, d/2, d/2, seg).translate([x, y, z0])

def to_tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(np.array(mm.vert_properties)[:, :3], np.array(mm.tri_verts), process=False)

def get_base_plate(base_dir):
    # Base OEM plate mesh: Z=0 is front face, Z>0 extends into dash cavity
    src = os.path.join(base_dir, "stls", "phone_mount", "sonoma_ball_plate(1).stl")
    tm = trimesh.load(src)
    return Manifold(Mesh(vert_properties=np.asarray(tm.vertices, dtype=np.float32),
                         tri_verts=np.asarray(tm.faces, dtype=np.uint32)))

# ----------------- 1. Magnetic Core Cubby -----------------
def generate_magnetic_dock(base_plate, depth=DEPTH):
    # Base plate has OEM flange & retention tabs (0 to 24mm depth)
    dock = base_plate
    
    # Outer box extension to full depth
    outer_box = rrect(CUBBY_W - 0.8, CUBBY_H - 0.8, 3.5).extrude(depth).translate([0, 0, 0])
    dock += outer_box
    
    # Hollow interior cavity cutting completely through front face
    cavity_w = CUBBY_W - 2 * WALL_T
    cavity_h = CUBBY_H - 2 * WALL_T
    cavity = rrect(cavity_w, cavity_h, 3.0).extrude(depth - FLOOR_T + 5.0).translate([0, 0, -5.0])
    dock -= cavity
    
    # Rear wire pass-through port (for USB-C / 12V harness)
    wire_port = rrect(18.0, 10.0, 3.0).extrude(FLOOR_T + 4.0).translate([0, 0, depth - FLOOR_T - 1.0])
    dock -= wire_port
    
    # 4 Corner Neodymium Magnet Bosses & Pockets (Front rim)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = sx * MAG_X
            py = sy * MAG_Y
            # Add solid boss pad in the corner
            pad = cyl(MAG_D + 3.0, 0.0, MAG_DEPTH + 1.5, px, py)
            dock += pad
            # Pocket void for 6mm x 3mm neodymium disc
            dock -= cyl(MAG_D, -1.0, MAG_DEPTH, px, py)
            
    return dock

# ----------------- 2. Stealth Magnet Stash Cover -----------------
def generate_stealth_cover():
    plate_t = 3.5
    lip_t = 2.0
    # Beveled front cover matching dash bezel profile (Z = -plate_t to 0)
    cover = rrect(CUBBY_W, CUBBY_H, 4.0).extrude(plate_t).translate([0, 0, -plate_t])
    
    # Inset locating rim (fits snugly into cubby opening from Z = 0 to lip_t)
    cavity_w = CUBBY_W - 2 * WALL_T - 0.5
    cavity_h = CUBBY_H - 2 * WALL_T - 0.5
    locating_rim = rrect(cavity_w, cavity_h, 2.5).extrude(lip_t).translate([0, 0, 0])
    
    # Relief cutouts on the locating rim so it clears the dock's corner magnet bosses
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = sx * MAG_X
            py = sy * MAG_Y
            locating_rim -= cyl(MAG_D + 3.8, -0.5, lip_t + 1.0, px, py)
    cover += locating_rim
    
    # 4 Neodymium Magnet Pockets (flush with rear mating face Z=0, recessed forward into cover plate)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = sx * MAG_X
            py = sy * MAG_Y
            cover -= cyl(MAG_D, -MAG_DEPTH, 0.05, px, py)
            
    # Bottom finger relief notch for easy pull-off
    notch = rrect(22.0, 8.0, 3.0).extrude(plate_t + 2.0).translate([0, -CUBBY_H/2 + 2.0, -plate_t - 1.0])
    cover -= notch
    return cover

# ----------------- 3. Magnetic MagSafe Charging Plate -----------------
def generate_magsafe_plate():
    cover = generate_stealth_cover()
    
    # MagSafe puck dimensions: 56.0mm dia x 5.5mm depth
    puck_d = 56.4
    puck_depth = 5.8
    tilt_rad = math.radians(15.0) # 15 deg tilted up toward driver
    
    # Angled mounting cradle boss on front of plate
    cradle_base = cyl(puck_d + 6.0, -puck_depth - 12.0, 0.0, 0, 0)
    # Rotate cradle 15 deg around X
    cradle_base = cradle_base.rotate([-15, 0, 0]).translate([0, 2.0, -3.0])
    
    # Hollow puck recess
    puck_void = cyl(puck_d, -puck_depth - 0.5, 1.0, 0, 0).rotate([-15, 0, 0]).translate([0, 2.0, -3.0])
    
    # Rear cable pass-through hole (5.0mm slot for USB-C wire)
    cable_slot = box(-3.5, 3.5, -5.0, 25.0, -15.0, 5.0).rotate([-15, 0, 0]).translate([0, 2.0, -3.0])
    
    part = cover + cradle_base - puck_void - cable_slot
    return part

# ----------------- 4. Magnetic 17mm Ball Plate -----------------
def generate_mag_ball_plate():
    cover = generate_stealth_cover()
    
    ball_d = 17.0
    stem_d = 11.0
    tilt_rad = math.radians(15.0)
    stem_len = 24.0
    
    bz = -stem_len * math.cos(tilt_rad) - 3.5
    by = stem_len * math.sin(tilt_rad)
    
    ball = Manifold.sphere(ball_d / 2.0, SEG).translate([0, by, bz])
    stem = Manifold.batch_hull([
        cyl(stem_d * 1.4, -6.0, 0.0, 0, 0),
        cyl(stem_d, bz, bz + 2.0, 0, by)
    ])
    
    keel = Manifold.batch_hull([
        Manifold.cube([stem_d * 0.7, 18.0, 3.0], center=True).translate([0, 0, -2.0]),
        Manifold.cube([stem_d * 0.5, stem_d, 5.0], center=True).translate([0, by, bz + 3.0])
    ])
    
    return cover + ball + stem + keel

# ----------------- 5. Push-In Slide Cartridge Cubby & Mount -----------------
def generate_slide_cubby(base_plate):
    dock = base_plate
    outer_box = rrect(CUBBY_W - 0.8, CUBBY_H - 0.8, 3.5).extrude(DEPTH).translate([0, 0, 0])
    dock += outer_box
    
    cavity_w = CUBBY_W - 2 * WALL_T
    cavity_h = CUBBY_H - 2 * WALL_T
    cavity = rrect(cavity_w, cavity_h, 3.0).extrude(DEPTH - FLOOR_T + 5.0).translate([0, 0, -5.0])
    dock -= cavity
    
    # Internal Slide Rails in top section
    # Left rail at -cavity_w/2, Right rail at +cavity_w/2
    rail_h = 4.0
    rail_t = 2.5
    rail_z = 45.0 # rails extend 45mm into cubby
    rail_y = cavity_h / 2 - 8.0 # upper position
    
    left_rail = box(-cavity_w/2 - 0.5, -cavity_w/2 + rail_t, rail_y - rail_h/2, rail_y + rail_h/2, 0.0, rail_z)
    right_rail = box(cavity_w/2 - rail_t, cavity_w/2 + 0.5, rail_y - rail_h/2, rail_y + rail_h/2, 0.0, rail_z)
    dock += left_rail + right_rail
    
    # Wire port
    wire_port = rrect(18.0, 10.0, 3.0).extrude(FLOOR_T + 4.0).translate([0, 0, DEPTH - FLOOR_T - 1.0])
    dock -= wire_port
    return dock

def generate_slide_phone_mount():
    cavity_w = CUBBY_W - 2 * WALL_T - 0.4 # clearance
    cartridge_l = 40.0
    cartridge_t = 6.0
    
    # Cartridge plate that slides into rails
    plate = rrect(cavity_w, cartridge_l, 2.5).extrude(cartridge_t).rotate([90, 0, 0]).translate([0, 0, 0])
    
    # Side grooves matching cubby rails
    groove_h = 4.6
    groove_d = 2.8
    groove_l = cartridge_l + 2.0
    left_grv = box(-cavity_w/2 - 1.0, -cavity_w/2 + groove_d, -groove_h/2, groove_h/2, -1.0, groove_l)
    right_grv = box(cavity_w/2 - groove_d, cavity_w/2 + 1.0, -groove_h/2, groove_h/2, -1.0, groove_l)
    plate = plate - left_grv - right_grv
    
    # Front stop flange
    flange = rrect(CUBBY_W - 2.0, 14.0, 2.5).extrude(3.0).translate([0, 0, -3.0])
    
    # 17mm Ball Mount on front
    ball_d = 17.0
    stem_d = 10.0
    ball = Manifold.sphere(ball_d / 2.0, SEG).translate([0, 8.0, -26.0])
    stem = Manifold.batch_hull([
        cyl(stem_d * 1.3, -3.0, 0.0, 0, 0),
        cyl(stem_d, -26.0, -24.0, 0, 8.0)
    ])
    
    return plate + flange + ball + stem

# ----------------- 6. Monolithic 2-in-1 Phone Cradle + Lower Cubby -----------------
def generate_integrated_phone_dock(base_plate):
    dock = base_plate
    outer_box = rrect(CUBBY_W - 0.8, CUBBY_H - 0.8, 3.5).extrude(DEPTH).translate([0, 0, 0])
    dock += outer_box
    
    # Lower sunglasses cavity
    low_cavity_w = CUBBY_W - 2 * WALL_T
    low_cavity_h = 22.0
    low_cavity = rrect(low_cavity_w, low_cavity_h, 3.0).extrude(DEPTH - FLOOR_T + 5.0).translate([0, -CUBBY_H/2 + low_cavity_h/2 + 2.5, -5.0])
    dock -= low_cavity
    
    # Upper Phone Holster (expands forward at 18 deg angle)
    # Fits modern phones up to 84mm wide x 14mm thick with case
    phone_w = 84.0
    phone_t = 15.0
    phone_depth = 55.0
    
    holster_hull = rrect(phone_w + 6.0, phone_t + 6.0, 4.0).extrude(phone_depth).rotate([-18, 0, 0]).translate([0, 8.0, -phone_depth * 0.85])
    dock += holster_hull
    
    # Phone pocket void
    phone_void = rrect(phone_w, phone_t, 3.0).extrude(phone_depth + 10.0).rotate([-18, 0, 0]).translate([0, 8.0, -phone_depth * 0.85 - 1.0])
    dock -= phone_void
    
    # Bottom USB-C charging slot
    cable_slot = rrect(24.0, 10.0, 3.0).extrude(20.0).rotate([-18, 0, 0]).translate([0, 8.0, -phone_depth * 0.85 - 5.0])
    dock -= cable_slot
    
    # Re-clean lower cavity in case holster protruded
    dock -= low_cavity
    return dock

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(base_dir, "stls", "dash_cubby")
    os.makedirs(out_dir, exist_ok=True)
    
    print("Loading base OEM plate mesh...")
    base_plate = get_base_plate(base_dir)
    
    print("1a. Generating S10_cubby_magnetic_dock.stl (140mm Deep Glasses Spec)...")
    dock_140 = generate_magnetic_dock(base_plate, depth=140.0)
    to_tm(dock_140).export(os.path.join(out_dir, "S10_cubby_magnetic_dock.stl"))
    
    print("1b. Generating S10_cubby_magnetic_dock_147mm.stl (147.2mm Max Depth Spec)...")
    dock_147 = generate_magnetic_dock(base_plate, depth=147.2)
    to_tm(dock_147).export(os.path.join(out_dir, "S10_cubby_magnetic_dock_147mm.stl"))
    
    print("2. Generating S10_cubby_mag_stealth_cover.stl...")
    stealth = generate_stealth_cover()
    to_tm(stealth).export(os.path.join(out_dir, "S10_cubby_mag_stealth_cover.stl"))
    
    print("3. Generating S10_cubby_mag_magsafe_plate.stl...")
    magsafe = generate_magsafe_plate()
    to_tm(magsafe).export(os.path.join(out_dir, "S10_cubby_mag_magsafe_plate.stl"))
    
    print("4. Generating S10_cubby_mag_ball_plate.stl...")
    ball_plate = generate_mag_ball_plate()
    to_tm(ball_plate).export(os.path.join(out_dir, "S10_cubby_mag_ball_plate.stl"))
    
    print("5. Generating S10_cubby_slide_dock.stl...")
    slide_dock = generate_slide_cubby(base_plate)
    to_tm(slide_dock).export(os.path.join(out_dir, "S10_cubby_slide_dock.stl"))
    
    print("6. Generating S10_slide_phone_mount.stl...")
    slide_mount = generate_slide_phone_mount()
    to_tm(slide_mount).export(os.path.join(out_dir, "S10_slide_phone_mount.stl"))
    
    print("7. Generating S10_cubby_integrated_phone_dock.stl...")
    combo = generate_integrated_phone_dock(base_plate)
    to_tm(combo).export(os.path.join(out_dir, "S10_cubby_integrated_phone_dock.stl"))
    
    print("\nAll 7 Modular Dash Cubby STLs Generated Successfully!")

if __name__ == "__main__":
    main()
