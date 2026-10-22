#!/usr/bin/env python3
"""
Tactical EDC Belt Sheath / Holster for Stanley 12-in-1 Multitool
Form-fitted directly from 3D photogrammetric scan geometry.

Features:
  - Form-fitting tool pocket with calibrated 0.6mm glide tolerance
  - Active cantilever spring detent with tactile click-lock bead
  - Integrated 1.75" (45mm) heavy-duty belt / pocket clip with retention tooth
  - Reinforcing stress-relief gusset on belt clip bridge
  - Bottom debris drainage & index-finger quick-draw push-up port
  - Integrated lower corner 550 paracord lanyard loop
  - Smooth rounded outer corners (R=6mm) for comfortable EDC carry
"""

import os, sys, math
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection, JoinType

SEG = 48

def rrect(w, h, r, seg=SEG):
    """2D Rounded Rectangle centered at origin."""
    r = min(r, w/2.0 - 0.1, h/2.0 - 0.1)
    return CrossSection.square([w - 2.0*r, h - 2.0*r], center=True).offset(r, JoinType.Round, 2.0, seg)

def build_stanley_sheath():
    # -------------------------------------------------------------------------
    # 1. CORE DIMENSIONS
    # -------------------------------------------------------------------------
    # Stanley 12-in-1 multitool scan: 105.0mm length, 43.8mm width, 18.5mm thickness
    # Cavity with 0.6mm glide clearance:
    CAV_W = 45.0   # mm inner width
    CAV_T = 19.6   # mm inner thickness
    CAV_H = 72.0   # mm inner pocket depth (leaves top 33mm of tool exposed for firm draw grip)
    CAV_R = 3.5    # mm corner radius

    # Outer wall thicknesses:
    WALL_X = 2.8   # mm side walls
    WALL_Y = 3.0   # mm front/back walls
    FLOOR_T = 3.5  # mm bottom floor thickness

    OUT_W = CAV_W + 2.0 * WALL_X  # 50.6 mm
    OUT_T = CAV_T + 2.0 * WALL_Y  # 25.6 mm
    OUT_H = CAV_H + FLOOR_T       # 75.5 mm
    OUT_R = CAV_R + 2.5           # 6.0 mm

    # -------------------------------------------------------------------------
    # 2. MAIN SHEATH BODY & CAVITY
    # -------------------------------------------------------------------------
    # Outer solid hull
    cs_out = rrect(OUT_W, OUT_T, OUT_R)
    body_solid = cs_out.extrude(OUT_H)

    # Inner cavity (starts at Z = FLOOR_T up to OUT_H + 5)
    cs_cav = rrect(CAV_W, CAV_T, CAV_R)
    cavity = cs_cav.extrude(OUT_H + 10.0).translate([0.0, 0.0, FLOOR_T])

    # Bottom drainage and quick-draw push-up hole:
    # 24mm wide x 10mm thick opening through floor
    cs_drain = rrect(24.0, 10.0, 3.5)
    drain_hole = cs_drain.extrude(FLOOR_T + 4.0).translate([0.0, 0.0, -2.0])

    sheath_hull = body_solid - cavity - drain_hole

    # -------------------------------------------------------------------------
    # 3. ACTIVE CANTILEVER CLICK-LOCK RETENTION SPRING
    # -------------------------------------------------------------------------
    # Compliant spring finger on the front face (Y = -OUT_T/2 = -12.8mm)
    # Finger root at Z = 24.0mm, top at Z = 60.0mm (36mm compliant beam)
    # Width = 12mm (X from -6.0 to +6.0)
    slot_t = 1.6  # mm slot clearance
    slit_l = Manifold.cube([slot_t, WALL_Y + 4.0, 36.0]).translate([-6.0 - slot_t, -OUT_T/2.0 - 2.0, 24.0])
    slit_r = Manifold.cube([slot_t, WALL_Y + 4.0, 36.0]).translate([6.0, -OUT_T/2.0 - 2.0, 24.0])
    slit_top = Manifold.cube([12.0 + 2.0*slot_t, WALL_Y + 4.0, slot_t]).translate([-6.0 - slot_t, -OUT_T/2.0 - 2.0, 60.0 - slot_t])
    spring_slots = slit_l + slit_r + slit_top

    sheath_hull = sheath_hull - spring_slots

    # Click-lock retention bead on the inside of the spring finger:
    # Located at Z = 52.0mm, protruding 1.2mm into cavity to snap into handle skeleton cutout.
    # Cavity front wall is at Y = -CAV_T/2 = -9.8mm.
    # Clamped to Y >= -12.8mm so outside remains perfectly flush and smooth.
    bead_raw = Manifold.sphere(3.2, 32).translate([0.0, -CAV_T/2.0 - 2.0, 52.0])
    bead_clamp = Manifold.cube([20.0, 10.0, 20.0]).translate([-10.0, -OUT_T/2.0, 52.0 - 10.0])
    bead = bead_raw ^ bead_clamp
    sheath_hull = sheath_hull + bead

    # -------------------------------------------------------------------------
    # 4. HEAVY-DUTY BELT / POCKET CLIP (1.75" / 45mm Belt Compatible)
    # -------------------------------------------------------------------------
    # Located on rear face (Y = +OUT_T/2 = +12.8mm)
    CLIP_W = 20.0  # mm clip width
    CLIP_GAP = 5.2 # mm belt clearance gap (fits thick leather / tactical webbing)
    CLIP_T = 3.2   # mm arm thickness
    CLIP_L = 54.0  # mm vertical clip length

    # Top bridge connecting sheath to clip:
    clip_bridge = Manifold.cube([CLIP_W, CLIP_GAP + CLIP_T, 8.0]).translate([
        -CLIP_W/2.0, OUT_T/2.0 - 0.5, OUT_H - 12.0
    ])

    # Reinforcing fillet gusset under the bridge to prevent stress concentration:
    gusset_pts = np.array([
        [0.0, 0.0],
        [0.0, -8.0],
        [CLIP_GAP, 0.0]
    ]) # CCW
    cs_gusset = CrossSection([gusset_pts])
    bridge_gusset = cs_gusset.extrude(CLIP_W).transform(np.array([
        [0, 0, 1, -CLIP_W/2.0],
        [1, 0, 0, OUT_T/2.0 - 0.5],
        [0, 1, 0, OUT_H - 12.0]
    ]))

    # Downward clip spine:
    clip_spine = Manifold.cube([CLIP_W, CLIP_T, CLIP_L]).translate([
        -CLIP_W/2.0, OUT_T/2.0 + CLIP_GAP, OUT_H - 12.0 - CLIP_L + 8.0
    ])

    # Inward retention barb / tooth at bottom of clip (CCW):
    tooth_pts = np.array([
        [0.0, 0.0],
        [0.0, 6.0],
        [-2.2, 3.0]
    ]) # CCW
    cs_tooth = CrossSection([tooth_pts])
    tooth = cs_tooth.extrude(CLIP_W).transform(np.array([
        [0, 0, 1, -CLIP_W/2.0],
        [1, 0, 0, OUT_T/2.0 + CLIP_GAP],
        [0, 1, 0, OUT_H - 12.0 - CLIP_L + 10.0]
    ]))

    # Outward bottom ski-ramp for easy one-handed belt mounting (CCW):
    ramp_pts = np.array([
        [0.0, 0.0],
        [0.0, -4.0],
        [3.5, -4.0]
    ]) # CCW
    cs_ramp = CrossSection([ramp_pts])
    ramp = cs_ramp.extrude(CLIP_W).transform(np.array([
        [0, 0, 1, -CLIP_W/2.0],
        [1, 0, 0, OUT_T/2.0 + CLIP_GAP + CLIP_T],
        [0, 1, 0, OUT_H - 12.0 - CLIP_L + 8.0]
    ]))

    clip_assembly = clip_bridge + bridge_gusset + clip_spine + tooth + ramp

    # -------------------------------------------------------------------------
    # 5. PARACORD / CARABINER LANYARD LUG (Lower Side Wall)
    # -------------------------------------------------------------------------
    # Lower corner tether attachment at Z = 14mm, with horizontal 5.0mm paracord hole
    lug_x = -OUT_W/2.0 - 3.5
    lug_z = 14.0
    lug_cyl = (Manifold.cylinder(8.0, 6.0, 6.0, 32)
               .rotate([90, 0, 0])
               .translate([lug_x, 4.0, lug_z]))
    lug_bridge = Manifold.cube([6.0, 8.0, 12.0]).translate([-OUT_W/2.0 - 4.0, -4.0, lug_z - 6.0])
    lug_hole = (Manifold.cylinder(12.0, 2.5, 2.5, 32)
                .rotate([90, 0, 0])
                .translate([lug_x, 6.0, lug_z]))
    lanyard_lug = (lug_cyl + lug_bridge) - lug_hole

    # -------------------------------------------------------------------------
    # 6. FINAL UNION & COMPILATION
    # -------------------------------------------------------------------------
    sheath = sheath_hull + clip_assembly + lanyard_lug
    return sheath

def export_sheath():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stls_dir = os.path.join(base_dir, "stls", "accessories")
    os.makedirs(stls_dir, exist_ok=True)

    print("Generating Stanley Multitool Tactical EDC Sheath...")
    sheath = build_stanley_sheath()
    mm = sheath.to_mesh()
    tm = trimesh.Trimesh(np.array(mm.vert_properties)[:, :3], np.array(mm.tri_verts), process=False)

    print(f"  Watertight: {tm.is_watertight}")
    print(f"  Faces: {len(tm.faces):,}, Vertices: {len(tm.vertices):,}")
    print(f"  Total Material Volume: {tm.volume / 1000.0:.2f} cm3")
    print(f"  Overall Extents: {tm.extents[0]:.1f} W x {tm.extents[1]:.1f} T x {tm.extents[2]:.1f} H mm")

    out_path = os.path.join(stls_dir, "stanley_multitool_tactical_sheath.stl")
    tm.export(out_path)
    print(f"Saved: {out_path}")

if __name__ == '__main__':
    export_sheath()
