#!/usr/bin/env python3
"""
Production 3D CAD generator for 1994-2004 GMC Sonoma / Chevy S10 Dashboard Phone Mounts:
  1. sonoma_plate_metal_ball.stl      - For metal 17mm ball stud with 1/4"-20 threaded male post
  2. sonoma_plate_printed_ball.stl    - For printed ball with front-accessible screws & captive nuts
  3. ball_17mm_frontmount.stl         - 17mm ball stud with front-access counter-bored screw holes (oriented on side)
  4. sonoma_plate_monolithic_ball.stl - 1-piece fused faceplate + 17mm ball (zero hardware)
"""
import math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, CrossSection

IN = 25.4
SEG = 96

def hex_prism(flats, depth):
    r = (flats / 2.0) / math.cos(math.pi / 6)
    pts = []
    for i in range(6):
        ang = i * (math.pi / 3) + (math.pi / 6)
        pts.append((r * math.cos(ang), r * math.sin(ang)))
    cs = CrossSection([pts])
    return cs.extrude(depth)

def cyl(d, z0, z1, x=0, y=0, seg=SEG):
    return Manifold.cylinder(z1 - z0, d/2, d/2, seg).translate([x, y, z0])

def to_tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(np.array(mm.vert_properties)[:, :3], np.array(mm.tri_verts), process=False)

def get_base_plate():
    # Base OEM plate mesh: Z=0 is front face, Z>0 extends into dash cavity
    src = "/mnt/c/Users/v-mariorivas/Downloads/sonoma_ball_plate(1).stl"
    tm = trimesh.load(src)
    return Manifold(Mesh(vert_properties=np.asarray(tm.vertices, dtype=np.float32), tri_verts=np.asarray(tm.faces, dtype=np.uint32)))

# 1. Plate for Metal Ball Stud (1/4"-20)
def generate_plate_metal_ball():
    m = get_base_plate()
    my = 8.0 # upper portion of plate for high phone clearance
    
    # Solid reinforced boss on rear
    boss = cyl(22.0, 0.0, 10.0, 0, my)
    m += boss
    
    # 1/4"-20 through-hole (6.6mm diameter)
    m -= cyl(6.6, -1.0, 11.0, 0, my)
    
    # Molded rear hex nut pocket (11.5mm flats, 6.0mm deep)
    hex_nut = hex_prism(11.5, 6.0).translate([0, my, 4.0])
    m -= hex_nut
    return m

# 2. Plate for Printed Ball (Front-Mounted Screws)
def generate_plate_printed_ball():
    m = get_base_plate()
    my = 8.0
    screw_spacing = 16.0
    screw_d = 3.6 # clearance for M3 or #6 screw
    nut_flats = 6.0 # M3 nut flats = 5.5mm (6.0mm with tolerance)
    
    # Solid boss behind mounting holes
    boss = cyl(22.0, 0.0, 9.0, 0, my)
    m += boss
    
    for sy in (-screw_spacing/2, screw_spacing/2):
        py = my + sy
        # Through hole
        m -= cyl(screw_d, -1.0, 10.0, 0, py)
        # Rear hex nut pocket (depth = 3.5mm)
        m -= hex_prism(nut_flats, 3.5).translate([0, py, 4.5])
        
    return m

# 3. 17mm Ball Stud with Front Screws (Printed on its side)
def generate_ball_17mm_frontmount():
    ball_d = 17.0
    stem_d = 11.0
    tilt_deg = 15.0
    tilt_rad = math.radians(tilt_deg)
    
    # Base flange that sits against the front faceplate
    flange_w, flange_h, flange_t = 16.0, 28.0, 4.5
    cs_base = CrossSection.square([flange_w - 6.0, flange_h - 6.0], center=True).offset(3.0)
    base = cs_base.extrude(flange_t)
    
    stem_len = 22.0
    bz = flange_t + stem_len * math.cos(tilt_rad)
    by = stem_len * math.sin(tilt_rad)
    
    ball = Manifold.sphere(ball_d / 2.0, SEG).translate([0, by, bz])
    
    # Stem
    stem = Manifold.batch_hull([
        cyl(stem_d * 1.3, flange_t - 0.1, flange_t + 2.0, 0, 0),
        cyl(stem_d, bz - 2.0, bz, 0, by)
    ])
    
    # Keel
    keel = Manifold.batch_hull([
        Manifold.cube([stem_d*0.7, flange_h*0.7, 2.1], center=True).translate([0, 0, flange_t + 1.0]),
        Manifold.cube([stem_d*0.5, stem_d, 5.0], center=True).translate([0, by, bz - 3.5])
    ])
    
    part = base + stem + ball + keel
    
    # Front counter-bored screw holes
    screw_spacing = 16.0
    screw_d = 3.6
    cb_d = 7.0
    cb_depth = 2.5
    
    for sy in (-screw_spacing/2, screw_spacing/2):
        part -= cyl(screw_d, -1.0, flange_t + 10.0, 0, sy)
        part -= cyl(cb_d, flange_t - cb_depth, flange_t + 10.0, 0, sy)
        
    return part

# 4. Monolithic Single-Piece Option
def generate_plate_monolithic():
    m = get_base_plate()
    my = 8.0
    ball_d = 17.0
    stem_d = 11.0
    tilt_deg = 15.0
    tilt_rad = math.radians(tilt_deg)
    
    stem_len = 23.0
    bz = -stem_len * math.cos(tilt_rad) # extends forward (-Z)
    by = my + stem_len * math.sin(tilt_rad) # tilted up (+Y)
    
    ball = Manifold.sphere(ball_d / 2.0, SEG).translate([0, by, bz])
    stem = Manifold.batch_hull([
        cyl(stem_d * 1.4, -2.0, 2.0, 0, my),
        cyl(stem_d, bz, bz + 2.0, 0, by)
    ])
    keel = Manifold.batch_hull([
        Manifold.cube([stem_d*0.7, 20.0, 3.0], center=True).translate([0, my, 0]),
        Manifold.cube([stem_d*0.5, stem_d, 5.0], center=True).translate([0, by, bz + 3.0])
    ])
    
    return m + ball + stem + keel

def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    print("Generating Dashboard Phone Mount STLs...")
    
    models = [
        ("sonoma_plate_metal_ball", generate_plate_metal_ball(), False),
        ("sonoma_plate_printed_ball", generate_plate_printed_ball(), False),
        ("ball_17mm_frontmount", generate_ball_17mm_frontmount(), True), # pre-orient on side
        ("sonoma_plate_monolithic_ball", generate_plate_monolithic(), False),
    ]
    
    for name, m, flip_side in models:
        t = to_tm(m)
        assert t.is_watertight, f"{name} is not watertight!"
        if flip_side:
            # Rotate 90 deg around Y axis so layer lines run longitudinally along neck
            t.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
        t.apply_translation(-t.bounds[0])
        p = os.path.join(out_dir, f"{name}.stl")
        t.export(p)
        e = t.extents / IN
        print(f"  [OK] {name}.stl: {e[0]:.2f}W x {e[1]:.2f}L x {e[2]:.2f}H in | Vol: {m.volume()/1000:.1f} cm3")

    print("\nAll Phone Mount STLs generated successfully in:", out_dir)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    main(out)
