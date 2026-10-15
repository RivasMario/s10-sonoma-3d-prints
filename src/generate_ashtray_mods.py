#!/usr/bin/env python3
"""
Parametric 3D CAD Generator for 1998-2004 Chevy S10 / GMC Sonoma Ashtray Conversions:
  1. S10_ashtray_usb_power_panel.stl   - Flush faceplate with standard 28.5mm (1-1/8") round hole for USB-C PD / Voltmeter socket
  2. S10_ashtray_deep_pocket.stl       - Deep organizer drop tray replacing the metal ash cup for keys/coins/AirPods
  3. S10_ashtray_combo_power_pocket.stl - 2-in-1: Left-side 28.5mm USB socket + Right-side drop-in card/key pocket
"""

import math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, CrossSection, JoinType

SEG = 96

# Factory 1998-2004 S10 Ashtray Drawer Dimensions
TRAY_W = 86.0    # mm outer width
TRAY_H = 46.0    # mm outer height
TRAY_DEPTH = 75.0 # mm depth into dash drawer
WALL_T = 2.8     # mm wall thickness
FLOOR_T = 3.0    # mm floor thickness

# Standard 12V Marine USB-C / Voltmeter Socket Diameter
USB_SOCKET_D = 28.8 # mm (for standard 28.5mm / 1-1/8" threaded cylindrical socket)

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

# 1. Flush USB-C Power Panel
def generate_ashtray_usb_panel():
    plate_t = 4.0
    rim_t = 12.0 # retention rim depth into ashtray tracks
    
    # Outer front bezel matching ashtray drawer face
    face = rrect(TRAY_W, TRAY_H, 4.0).extrude(plate_t).translate([0, 0, -plate_t])
    
    # Inset locating body that clips into drawer rails
    body_w = TRAY_W - 3.0
    body_h = TRAY_H - 3.0
    body = rrect(body_w, body_h, 3.0).extrude(rim_t).translate([0, 0, 0])
    
    # Hollow interior to allow rear lock-nut access
    hollow_w = body_w - 2 * WALL_T
    hollow_h = body_h - 2 * WALL_T
    hollow = rrect(hollow_w, hollow_h, 2.5).extrude(rim_t + 2.0).translate([0, 0, 1.0])
    
    panel = (face + body) - hollow
    
    # Centered 28.8mm hole for standard USB-C PD / Voltmeter socket
    usb_hole = cyl(USB_SOCKET_D, -plate_t - 1.0, rim_t + 1.0, 0, 0)
    panel -= usb_hole
    
    # Rear wire clearance notches
    notch = box(-15.0, 15.0, -body_h/2 - 1.0, body_h/2 + 1.0, rim_t - 4.0, rim_t + 2.0)
    panel -= notch
    
    return panel

# 2. Deep Drop-in Organizer Pocket
def generate_ashtray_deep_pocket():
    # Outer box
    outer = rrect(TRAY_W - 1.0, TRAY_H - 1.0, 4.0).extrude(TRAY_DEPTH).translate([0, 0, 0])
    
    # Front rim flange
    flange = rrect(TRAY_W + 3.0, TRAY_H + 3.0, 4.5).extrude(3.5).translate([0, 0, -3.5])
    
    # Interior cavity
    cav_w = TRAY_W - 2 * WALL_T
    cav_h = TRAY_H - 2 * WALL_T
    cavity = rrect(cav_w, cav_h, 3.0).extrude(TRAY_DEPTH - FLOOR_T + 5.0).translate([0, 0, -5.0])
    
    pocket = (outer + flange) - cavity
    
    # Internal divider for coin / key separation
    divider = box(-cav_w/2, cav_w/2, -1.2, 1.2, 0.0, TRAY_DEPTH - FLOOR_T - 10.0)
    pocket += divider
    
    # Bottom finger lift groove
    return pocket

# 3. 2-in-1 Combo: Left USB-C Power Port + Right Deep Pocket
def generate_ashtray_combo():
    outer = rrect(TRAY_W - 1.0, TRAY_H - 1.0, 4.0).extrude(TRAY_DEPTH).translate([0, 0, 0])
    flange = rrect(TRAY_W + 3.0, TRAY_H + 3.0, 4.5).extrude(3.5).translate([0, 0, -3.5])
    
    # Left power socket housing (recessed depth 38mm for socket body and locknut)
    usb_x = -TRAY_W / 4.0
    usb_hollow = cyl(35.0, 0.0, 45.0, usb_x, 0)
    usb_hole = cyl(USB_SOCKET_D, -5.0, 5.0, usb_x, 0)
    wire_exit = cyl(16.0, 40.0, TRAY_DEPTH + 5.0, usb_x, 0)
    
    # Right deep pocket for keys / cards
    pocket_x = TRAY_W / 4.0
    pocket_w = TRAY_W / 2.0 - WALL_T - 1.0
    pocket_h = TRAY_H - 2 * WALL_T
    pocket_cav = rrect(pocket_w, pocket_h, 3.0).extrude(TRAY_DEPTH - FLOOR_T + 5.0).translate([pocket_x, 0, -5.0])
    
    combo = (outer + flange) - usb_hollow - usb_hole - wire_exit - pocket_cav
    return combo

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(base_dir, "stls", "ashtray")
    os.makedirs(out_dir, exist_ok=True)
    
    print("1. Generating S10_ashtray_usb_power_panel.stl...")
    p1 = generate_ashtray_usb_panel()
    to_tm(p1).export(os.path.join(out_dir, "S10_ashtray_usb_power_panel.stl"))
    
    print("2. Generating S10_ashtray_deep_pocket.stl...")
    p2 = generate_ashtray_deep_pocket()
    to_tm(p2).export(os.path.join(out_dir, "S10_ashtray_deep_pocket.stl"))
    
    print("3. Generating S10_ashtray_combo_power_pocket.stl...")
    p3 = generate_ashtray_combo()
    to_tm(p3).export(os.path.join(out_dir, "S10_ashtray_combo_power_pocket.stl"))
    
    print("All 3 Ashtray STLs Generated Successfully!")

if __name__ == "__main__":
    main()
