#!/usr/bin/env python3
"""
High-Resolution Studio CAD Multi-View Render for 1994-1997 Sonoma / S10 True Wedge Replacement Drawer
"""

import os, sys
import numpy as np
from stl import mesh
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from render_smooth_cad import render_mesh_studio

def render_wedge_showcase():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stl_path = os.path.join(base_dir, "stls", "ashtray", "sonoma_1995_true_wedge_drawer.stl")
    imgs_dir = os.path.join(base_dir, "images")
    os.makedirs(imgs_dir, exist_ok=True)

    # 1. 3/4 Isometric Front View
    m_iso = mesh.Mesh.from_file(stl_path)
    m_iso.rotate(np.array([1.0, 0.0, 0.0]), np.radians(90))
    m_iso.rotate(np.array([0.0, 1.0, 0.0]), np.radians(35))
    m_iso.rotate(np.array([1.0, 0.0, 0.0]), np.radians(-20))
    c_iso = np.full((len(m_iso.v0), 3), [46, 54, 64], dtype=np.float32)

    img_iso = render_mesh_studio(
        m_iso.v0, m_iso.v1, m_iso.v2, c_iso,
        W=1000, H=800, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=0.78, crease_deg=30.0
    )

    # 2. Side Profile View (exact vehicle orientation)
    m_side = mesh.Mesh.from_file(stl_path)
    R_side = np.array([
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0]
    ])
    for attr in ['v0', 'v1', 'v2']:
        setattr(m_side, attr, getattr(m_side, attr) @ R_side.T)
    c_side = np.full((len(m_side.v0), 3), [42, 70, 92], dtype=np.float32) # Tech Slate Blue

    img_side = render_mesh_studio(
        m_side.v0, m_side.v1, m_side.v2, c_side,
        W=900, H=800, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=0.80, crease_deg=30.0
    )

    # 3. Underside / Rear 3/4 View (showing wedge slope, rails, stop lugs)
    m_rear = mesh.Mesh.from_file(stl_path)
    m_rear.rotate(np.array([1.0, 0.0, 0.0]), np.radians(90))
    m_rear.rotate(np.array([0.0, 1.0, 0.0]), np.radians(145))
    m_rear.rotate(np.array([1.0, 0.0, 0.0]), np.radians(25))
    c_rear = np.full((len(m_rear.v0), 3), [58, 66, 76], dtype=np.float32)

    img_rear = render_mesh_studio(
        m_rear.v0, m_rear.v1, m_rear.v2, c_rear,
        W=900, H=800, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=0.82, crease_deg=30.0
    )

    # Combine into a panoramic 3-panel studio showcase
    total_w = 1000 + 900 + 900
    total_h = 800
    canvas = Image.new("RGB", (total_w, total_h), (245, 247, 250))
    canvas.paste(img_iso, (0, 0))
    canvas.paste(img_side, (1000, 0))
    canvas.paste(img_rear, (1900, 0))

    out_showcase = os.path.join(imgs_dir, "cad_render_1995_true_wedge_drawer.png")
    canvas.save(out_showcase, quality=95)
    print(f"Showcase banner saved: {out_showcase}")

    # Also save the individual isometric image
    out_iso = os.path.join(imgs_dir, "cad_render_1995_true_wedge_iso.png")
    img_iso.save(out_iso, quality=95)
    print(f"Isometric view saved: {out_iso}")

if __name__ == '__main__':
    render_wedge_showcase()
