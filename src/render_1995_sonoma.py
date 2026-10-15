#!/usr/bin/env python3
"""
Render high-resolution CAD studio images for 1995 GMC Sonoma models:
- Ashtray drop-in inserts (USB-C pod, 2-in-1 combo, deep EDC pocket)
- Bench seat cupholder upgrades (30/40oz tumbler sleeve, Fastback 6-in-1 caddy, 52mm stilt)
"""

import os, sys
import numpy as np
from stl import mesh
from PIL import Image

# Import render_mesh_studio from render_smooth_cad
sys.path.insert(0, os.path.dirname(__file__))
from render_smooth_cad import render_mesh_studio

def render_ashtray_inserts(usb_path, combo_path, deep_path, out_path):
    print("Rendering 1995 Sonoma Ashtray Drop-Ins Studio CAD...")
    m_usb = mesh.Mesh.from_file(usb_path)
    m_combo = mesh.Mesh.from_file(combo_path)
    m_deep = mesh.Mesh.from_file(deep_path)

    # In generate_1995_sonoma_mods.py, +Z is up (flange at Z=0..3, pocket at Z=-42..0).
    # Rotate around Z so the front edge faces forward/left
    for m in [m_usb, m_combo, m_deep]:
        m.rotate([0, 0, 1], np.radians(-25))

    # Arrange along X axis: USB on left, Combo in center, Deep Pocket on right
    xs = [-105.0, 0.0, 105.0]
    parts = [m_usb, m_combo, m_deep]
    for p, target_x in zip(parts, xs):
        c = np.mean(np.vstack([p.v0, p.v1, p.v2]), axis=0)
        p.translate([-c[0] + target_x, -c[1], -c[2]])

    v0 = np.vstack([m_usb.v0, m_combo.v0, m_deep.v0])
    v1 = np.vstack([m_usb.v1, m_combo.v1, m_deep.v1])
    v2 = np.vstack([m_usb.v2, m_combo.v2, m_deep.v2])

    part_id = np.zeros(len(v0), dtype=np.int32)
    i1 = len(m_usb.v0)
    i2 = i1 + len(m_combo.v0)
    part_id[i1:i2] = 1
    part_id[i2:] = 2

    colors = np.zeros((len(v0), 3), dtype=np.float32)
    colors[:i1] = [45, 95, 145]     # USB pod: Tech Blue
    colors[i1:i2] = [48, 110, 85]   # Combo: Slate Green
    colors[i2:] = [54, 58, 66]      # Deep Pocket: Anthracite Black

    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1600, H=850, elev_deg=32, azim_deg=20, roll_deg=0,
        zoom_factor=0.92, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

def render_cupholder_inserts(sleeve_path, caddy_path, stilt_path, out_path):
    print("Rendering 1995 Sonoma Cupholder Solutions Studio CAD...")
    m_sleeve = mesh.Mesh.from_file(sleeve_path)
    m_caddy = mesh.Mesh.from_file(caddy_path)
    m_stilt = mesh.Mesh.from_file(stilt_path)

    # In generate_1995_sonoma_mods.py, +Z is up (sleeve rim at +50, caddy rim at +45, stilt at +52).
    # Rotate around Z so the tumbler handle slot and Fastback holster are clearly visible.
    m_sleeve.rotate([0, 0, 1], np.radians(45))
    m_caddy.rotate([0, 0, 1], np.radians(-25))
    m_stilt.rotate([0, 0, 1], np.radians(30))

    xs = [-115.0, 0.0, 115.0]
    parts = [m_sleeve, m_caddy, m_stilt]
    for p, target_x in zip(parts, xs):
        c = np.mean(np.vstack([p.v0, p.v1, p.v2]), axis=0)
        p.translate([-c[0] + target_x, -c[1], -c[2]])

    v0 = np.vstack([m_sleeve.v0, m_caddy.v0, m_stilt.v0])
    v1 = np.vstack([m_sleeve.v1, m_caddy.v1, m_stilt.v1])
    v2 = np.vstack([m_sleeve.v2, m_caddy.v2, m_stilt.v2])

    part_id = np.zeros(len(v0), dtype=np.int32)
    i1 = len(m_sleeve.v0)
    i2 = i1 + len(m_caddy.v0)
    part_id[i1:i2] = 1
    part_id[i2:] = 2

    colors = np.zeros((len(v0), 3), dtype=np.float32)
    colors[:i1] = [54, 58, 66]      # Tumbler Sleeve: Anthracite Black
    colors[i1:i2] = [180, 40, 30]   # Fastback Caddy: Milwaukee Red Accent
    colors[i2:] = [40, 42, 46]      # 52mm Stilt: Textured Matte Black

    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1600, H=850, elev_deg=30, azim_deg=-10, roll_deg=0,
        zoom_factor=0.92, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stls = os.path.join(base, "stls")
    imgs = os.path.join(base, "images")
    os.makedirs(imgs, exist_ok=True)

    usb_stl = os.path.join(stls, "ashtray", "sonoma_1995_ashtray_usb_power.stl")
    combo_stl = os.path.join(stls, "ashtray", "sonoma_1995_ashtray_combo_power.stl")
    deep_stl = os.path.join(stls, "ashtray", "sonoma_1995_ashtray_edc_pocket.stl")

    sleeve_stl = os.path.join(stls, "cupholder", "sonoma_cupholder_tumbler_sleeve.stl")
    caddy_stl = os.path.join(stls, "cupholder", "sonoma_cupholder_fastback_caddy.stl")
    stilt_stl = os.path.join(stls, "cupholder", "sonoma_glide_stilt_52mm.stl")

    render_ashtray_inserts(usb_stl, combo_stl, deep_stl, os.path.join(imgs, "cad_render_1995_ashtray.png"))
    render_cupholder_inserts(sleeve_stl, caddy_stl, stilt_stl, os.path.join(imgs, "cad_render_1995_cupholder.png"))

if __name__ == "__main__":
    main()
