#!/usr/bin/env python3
"""
Exports clean, perfectly symmetrical dashboard phone mount STLs:
  1. sonoma_plate_monolithic_symmetrical.stl - 1-piece fused plate + centered 17mm ball + centered USB-C slot
  2. sonoma_plate_metal_ball.stl             - Updated with clean centered 1/4"-20 hole & hex nut pocket + centered USB-C slot
"""
import math, os
import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, CrossSection, JoinType

SEG = 96
IN = 25.4

def to_tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(np.array(mm.vert_properties)[:, :3], np.array(mm.tri_verts), process=False)

def rrect(w, l, rr, seg=48):
    rr = max(0.05, min(rr, w/2 - 0.01, l/2 - 0.01))
    return CrossSection.square([w - 2*rr, l - 2*rr], center=True).offset(rr, JoinType.Round, 2.0, seg)

def cyl(d, z0, z1, x=0, y=0, seg=SEG):
    return Manifold.cylinder(z1 - z0, d/2, d/2, seg).translate([x, y, z0])

def hex_prism(flats, depth):
    r = (flats / 2.0) / math.cos(math.pi / 6)
    pts = []
    for i in range(6):
        ang = i * (math.pi / 3) + (math.pi / 6)
        pts.append((r * math.cos(ang), r * math.sin(ang)))
    cs = CrossSection([pts])
    return cs.extrude(depth)

def get_clean_symmetrical_base():
    src = "/mnt/c/Users/v-mariorivas/Downloads/sonoma_ball_plate(1).stl"
    tm = trimesh.load(src)
    base = Manifold(Mesh(vert_properties=np.asarray(tm.vertices, dtype=np.float32), tri_verts=np.asarray(tm.faces, dtype=np.uint32)))
    
    # 1. Fill in the old asymmetric left-biased opening completely
    plug = rrect(30.0, 34.0, 4.0).extrude(10.0).translate([0, 2.0, 0.0])
    m = base + plug
    
    # 2. Cut a clean, DEAD-CENTER USB-C cable slot (X=0, Y=-9.0mm)
    # 8.0mm wide x 14.0mm tall
    slot = rrect(8.0, 14.0, 3.0).extrude(16.0).translate([0, -9.0, -3.0])
    m -= slot
    return m

def make_monolithic():
    m = get_clean_symmetrical_base()
    
    # 17mm ball on stem, centered in X (X=0), positioned in upper half (Y=+7.5mm)
    ball_d = 17.0
    stem_d = 11.5
    tilt_rad = math.radians(15.0)
    stem_len = 23.0
    
    # Extends forward (-Z in base plate coordinates)
    bz = -stem_len * math.cos(tilt_rad)
    by = 7.5 + stem_len * math.sin(tilt_rad)
    
    ball = Manifold.sphere(ball_d / 2.0, SEG).translate([0, by, bz])
    stem = Manifold.batch_hull([
        cyl(stem_d * 1.4, -2.0, 2.0, 0, 7.5),
        cyl(stem_d, bz, bz + 2.0, 0, by)
    ])
    keel = Manifold.batch_hull([
        Manifold.cube([stem_d*0.7, 18.0, 3.0], center=True).translate([0, 7.5, 0.5]),
        Manifold.cube([stem_d*0.5, stem_d, 5.0], center=True).translate([0, by, bz + 3.0])
    ])
    return m + ball + stem + keel

def make_metal_ball_plate():
    m = get_clean_symmetrical_base()
    my = 7.5
    
    # Solid reinforced boss on rear
    boss = cyl(22.0, 0.0, 10.0, 0, my)
    m += boss
    
    # Dead-center 1/4"-20 through-hole (6.6mm)
    m -= cyl(6.6, -2.0, 11.0, 0, my)
    
    # Dead-center 1/4"-20 hex nut pocket (11.5mm flats, 6.0mm deep)
    m -= hex_prism(11.5, 6.0).translate([0, my, 4.0])
    return m

def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    print("Exporting Clean Symmetrical Dashboard Phone Mount STLs...")
    
    # 1. Monolithic
    mono = make_monolithic()
    tm_mono = to_tm(mono)
    assert tm_mono.is_watertight, "Monolithic mesh not watertight!"
    tm_mono.apply_translation(-tm_mono.bounds[0])
    p1 = os.path.join(out_dir, "sonoma_plate_monolithic_symmetrical.stl")
    tm_mono.export(p1)
    e1 = tm_mono.extents / IN
    print(f"  [OK] sonoma_plate_monolithic_symmetrical.stl: {e1[0]:.2f}W x {e1[1]:.2f}L x {e1[2]:.2f}H in | {tm_mono.volume/1000:.1f} cm3")

    # 2. Metal Ball Plate
    metal = make_metal_ball_plate()
    tm_metal = to_tm(metal)
    assert tm_metal.is_watertight, "Metal ball plate mesh not watertight!"
    tm_metal.apply_translation(-tm_metal.bounds[0])
    p2 = os.path.join(out_dir, "sonoma_plate_metal_ball_symmetrical.stl")
    tm_metal.export(p2)
    # Also overwrite the previous metal plate with this clean symmetrical version
    tm_metal.export(os.path.join(out_dir, "sonoma_plate_metal_ball.stl"))
    e2 = tm_metal.extents / IN
    print(f"  [OK] sonoma_plate_metal_ball_symmetrical.stl: {e2[0]:.2f}W x {e2[1]:.2f}L x {e2[2]:.2f}H in | {tm_metal.volume/1000:.1f} cm3")

    print("\nAll symmetrical STLs saved to:", out_dir)

if __name__ == "__main__":
    main("/mnt/c/Users/v-mariorivas/Downloads")
