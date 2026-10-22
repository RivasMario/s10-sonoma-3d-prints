#!/usr/bin/env python3
"""
High-Resolution Studio CAD Multi-View Presentation for Stanley Multitool Tactical EDC Sheath
2x2 Studio Grid:
  [Top-Left]     3/4 Front Isometric (Active cantilever spring detent & lanyard loop)
  [Top-Right]    Seated EDC Assembly (Stanley 12-in-1 multitool locked inside holster)
  [Bottom-Left]  3/4 Rear Perspective (1.75" heavy-duty belt clip, bridge gusset & barb)
  [Bottom-Right] Underside Tactical View (Index-finger quick-draw & drainage port)
"""

import os, sys
import numpy as np
from stl import mesh
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from render_smooth_cad import render_mesh_studio

def make_view_matrix(yaw_deg, pitch_deg):
    yaw = np.radians(yaw_deg)
    pitch = np.radians(pitch_deg)
    R_yaw = np.array([
        [np.cos(yaw), 0, np.sin(yaw)],
        [0, 1, 0],
        [-np.sin(yaw), 0, np.cos(yaw)]
    ])
    R_pitch = np.array([
        [1, 0, 0],
        [0, np.cos(pitch), -np.sin(pitch)],
        [0, np.sin(pitch), np.cos(pitch)]
    ])
    R_init = np.array([
        [1, 0, 0],
        [0, 0, 1],
        [0, -1, 0]
    ])
    return R_pitch @ R_yaw @ R_init

def render_sheath_showcase():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stl_path = os.path.join(base_dir, "stls", "accessories", "stanley_multitool_tactical_sheath.stl")
    tool_path = os.path.join(base_dir, "scratch", "stanley_tool_cad.stl")
    imgs_dir = os.path.join(base_dir, "images")
    os.makedirs(imgs_dir, exist_ok=True)

    m = mesh.Mesh.from_file(stl_path)
    tool_m = mesh.Mesh.from_file(tool_path)
    tool_m.z += 3.5  # Rest on floor of sheath

    PANEL_W, PANEL_H = 1000, 900

    # -------------------------------------------------------------------------
    # Panel 1: Front 3/4 Isometric (Detent & Lanyard Loop)
    # -------------------------------------------------------------------------
    R_f = make_view_matrix(yaw_deg=-25, pitch_deg=18)
    v0_f = m.v0 @ R_f.T
    v1_f = m.v1 @ R_f.T
    v2_f = m.v2 @ R_f.T
    c_f = np.full((len(m.v0), 3), [46, 54, 66], dtype=np.float32) # Tactical Slate Grey

    img_front = render_mesh_studio(
        v0_f, v1_f, v2_f, c_f,
        W=PANEL_W, H=PANEL_H, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=0.82, crease_deg=30.0
    )

    # -------------------------------------------------------------------------
    # Panel 2: Seated EDC Assembly (Stanley Multitool Locked in Holster)
    # -------------------------------------------------------------------------
    R_ass = make_view_matrix(yaw_deg=-28, pitch_deg=20)
    v0_sf = m.v0 @ R_ass.T
    v1_sf = m.v1 @ R_ass.T
    v2_sf = m.v2 @ R_ass.T
    c_sf = np.full((len(m.v0), 3), [46, 54, 66], dtype=np.float32)

    v0_tf = tool_m.v0 @ R_ass.T
    v1_tf = tool_m.v1 @ R_ass.T
    v2_tf = tool_m.v2 @ R_ass.T
    c_tf = np.full((len(tool_m.v0), 3), [212, 218, 226], dtype=np.float32) # Stainless Steel

    v0_tot = np.vstack([v0_sf, v0_tf])
    v1_tot = np.vstack([v1_sf, v1_tf])
    v2_tot = np.vstack([v2_sf, v2_tf])
    c_tot = np.vstack([c_sf, c_tf])
    p_ids = np.hstack([np.zeros(len(v0_sf), dtype=np.int32), np.ones(len(v0_tf), dtype=np.int32)])

    img_assembly = render_mesh_studio(
        v0_tot, v1_tot, v2_tot, c_tot,
        W=PANEL_W, H=PANEL_H, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=0.82, crease_deg=30.0, is_part_id=p_ids
    )

    # -------------------------------------------------------------------------
    # Panel 3: Rear 3/4 Perspective (1.75" Belt Clip, Gusset, Retention Barb)
    # -------------------------------------------------------------------------
    R_r = make_view_matrix(yaw_deg=155, pitch_deg=18)
    v0_r = m.v0 @ R_r.T
    v1_r = m.v1 @ R_r.T
    v2_r = m.v2 @ R_r.T
    c_r = np.full((len(m.v0), 3), [52, 60, 72], dtype=np.float32)

    img_rear = render_mesh_studio(
        v0_r, v1_r, v2_r, c_r,
        W=PANEL_W, H=PANEL_H, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=0.82, crease_deg=30.0
    )

    # -------------------------------------------------------------------------
    # Panel 4: Underside Tactical View (Drainage / Index Finger Push-Up Port)
    # -------------------------------------------------------------------------
    R_b = make_view_matrix(yaw_deg=-20, pitch_deg=-52)
    v0_b = m.v0 @ R_b.T
    v1_b = m.v1 @ R_b.T
    v2_b = m.v2 @ R_b.T
    c_b = np.full((len(m.v0), 3), [50, 58, 70], dtype=np.float32)

    img_bot = render_mesh_studio(
        v0_b, v1_b, v2_b, c_b,
        W=PANEL_W, H=PANEL_H, elev_deg=0, azim_deg=0, roll_deg=0,
        zoom_factor=0.80, crease_deg=30.0
    )

    # -------------------------------------------------------------------------
    # Assemble 2x2 Showcase Canvas
    # -------------------------------------------------------------------------
    pad = 12
    grid_w = PANEL_W * 2 + pad * 3
    grid_h = PANEL_H * 2 + pad * 3
    canvas = Image.new("RGB", (grid_w, grid_h), (235, 238, 243))

    canvas.paste(img_front, (pad, pad))
    canvas.paste(img_assembly, (PANEL_W + pad * 2, pad))
    canvas.paste(img_rear, (pad, PANEL_H + pad * 2))
    canvas.paste(img_bot, (PANEL_W + pad * 2, PANEL_H + pad * 2))

    out_path = os.path.join(imgs_dir, "cad_render_stanley_sheath.png")
    canvas.save(out_path, quality=95)
    print(f"Saved 2x2 Sheath Studio Showcase to: {out_path}")

if __name__ == '__main__':
    render_sheath_showcase()
