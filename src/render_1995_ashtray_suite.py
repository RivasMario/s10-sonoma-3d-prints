#!/usr/bin/env python3
"""
Render high-resolution Studio CAD image comparing the 1995 Sonoma Ashtray Suite:
1. Full Slide-Out Vault Drawer (replaces OEM drawer, 160mm deep storage)
2. Cockpit Dual USB-C Fast-Charging Faceplate (solid flush mount with Rocker Switch)
3. Stock Drawer Drop-In Dual-Compartment Organizer (for keeping factory drawer)
4. 12V Cigarette Lighter to Dual USB-C Flush-Mount Conversion Bushing
"""

import os, sys
import numpy as np
from stl import mesh
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from render_smooth_cad import render_mesh_studio

def render_ashtray_suite():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stls = os.path.join(base, "stls", "ashtray")
    imgs = os.path.join(base, "images")
    os.makedirs(imgs, exist_ok=True)

    vault_path = os.path.join(stls, "sonoma_1995_ashtray_vault_drawer.stl")
    plate_path = os.path.join(stls, "sonoma_1995_ashtray_charging_plate.stl")
    stock_path = os.path.join(stls, "sonoma_1995_ashtray_stock_organizer.stl")
    lighter_path = os.path.join(stls, "sonoma_1995_lighter_usbc_adapter.stl")

    m_vault = mesh.Mesh.from_file(vault_path)
    m_plate = mesh.Mesh.from_file(plate_path)
    m_stock = mesh.Mesh.from_file(stock_path)
    m_lighter = mesh.Mesh.from_file(lighter_path)

    # In raw STL coords:
    # +Z is top of drawer/organizer, -Z is bottom floor
    # min Y is front faceplate (facing driver), max Y is rear (inside dash)
    #
    # Rotate around X by +64 deg (equivalent to 90 deg up, pitched down 26 deg to look into top cavity):
    # - Top (+Z) goes to +Y (up) and tilts towards viewer (+Z)
    # - Front (min Y) faces towards viewer (+Z)
    # - Rear (max Y) goes deep into screen (-Z)
    for m in [m_vault, m_plate, m_stock]:
        m.rotate(np.array([1.0, 0.0, 0.0]), np.radians(64))
        # Turn around Y by -25 deg so the front faceplate turns towards front-right
        m.rotate(np.array([0.0, 1.0, 0.0]), np.radians(-25))

    # For lighter adapter:
    # Stem is at -Z, front cup is at +Z.
    # We want front cup opening facing up and toward the viewer:
    m_lighter.rotate(np.array([1.0, 0.0, 0.0]), np.radians(-45))
    m_lighter.rotate(np.array([0.0, 1.0, 0.0]), np.radians(-25))

    # Center each part and arrange along Screen X
    xs = [-165.0, -35.0, 80.0, 175.0]
    parts = [m_vault, m_plate, m_stock, m_lighter]

    for p, target_x in zip(parts, xs):
        all_v = np.vstack([p.v0, p.v1, p.v2])
        c = np.mean(all_v, axis=0)
        p.translate([-c[0] + target_x, -c[1], -c[2]])

    v0 = np.vstack([p.v0 for p in parts])
    v1 = np.vstack([p.v1 for p in parts])
    v2 = np.vstack([p.v2 for p in parts])

    lengths = [len(p.v0) for p in parts]
    part_id = np.zeros(len(v0), dtype=np.int32)
    colors = np.zeros((len(v0), 3), dtype=np.float32)

    cur = 0
    # 1. Vault Drawer: Sleek Charcoal Black
    part_id[cur:cur+lengths[0]] = 0
    colors[cur:cur+lengths[0]] = [54, 58, 66]
    cur += lengths[0]

    # 2. Charging Plate: Precision Tech Blue / Anodized Cyan
    part_id[cur:cur+lengths[1]] = 1
    colors[cur:cur+lengths[1]] = [36, 96, 152]
    cur += lengths[1]

    # 3. Stock Organizer: Slate Green
    part_id[cur:cur+lengths[2]] = 2
    colors[cur:cur+lengths[2]] = [46, 112, 88]
    cur += lengths[2]

    # 4. Lighter Adapter: Warm Amber Bronze
    part_id[cur:cur+lengths[3]] = 3
    colors[cur:cur+lengths[3]] = [185, 125, 45]

    out_path = os.path.join(imgs, "cad_render_1995_ashtray_suite.png")
    print("Rendering Ashtray Suite CAD...")
    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1920, H=850, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=1.45, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    render_ashtray_suite()
