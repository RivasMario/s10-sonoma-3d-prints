#!/usr/bin/env python3
"""
Direct 3D CAD mesh renderer for 1994-2004 Chevy S10 / GMC Sonoma 3D Printed Accessories.
Uses numpy-stl and matplotlib to render crisp CAD studio snapshots directly from the
actual physical geometry STL files.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh

KEY_LIGHT = np.array([0.45, -0.65, 0.75])
KEY_LIGHT /= np.linalg.norm(KEY_LIGHT)

FILL_LIGHT = np.array([-0.50, 0.45, 0.35])
FILL_LIGHT /= np.linalg.norm(FILL_LIGHT)

def compute_shaded_colors(m, base_rgb, key_light=KEY_LIGHT, fill_light=FILL_LIGHT, ambient=0.28):
    normals = m.normals / np.maximum(np.linalg.norm(m.normals, axis=1, keepdims=True), 1e-6)
    diff_key = np.maximum(0, np.dot(normals, key_light))
    diff_fill = np.maximum(0, np.dot(normals, fill_light))
    intensity = ambient + 0.52 * diff_key + 0.20 * diff_fill
    colors = intensity[:, np.newaxis] * base_rgb
    return np.clip(colors, 0, 1)

def set_tight_3d_bounds(ax, pts, zoom_factor=0.38):
    center = np.mean(pts, axis=0)
    spans = np.ptp(pts, axis=0)
    max_span = np.max(spans) * zoom_factor
    ax.set_xlim(center[0] - max_span, center[0] + max_span)
    ax.set_ylim(center[1] - max_span, center[1] + max_span)
    ax.set_zlim(center[2] - max_span, center[2] + max_span)

def render_cupholder_assembly(deck_path, stilt_path, out_path):
    print("Rendering Cupholder Assembly CAD Snapshot...")
    deck = mesh.Mesh.from_file(deck_path)
    stilt = mesh.Mesh.from_file(stilt_path)
    
    stilt.translate([-85.0 / 2, -60.0 / 2, 0])
    deck.translate([0, 0, 290.2])
    
    fig = plt.figure(figsize=(11, 10), dpi=180)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#141517')
    fig.patch.set_facecolor('#141517')
    
    deck_colors = compute_shaded_colors(deck, np.array([0.94, 0.54, 0.15]))
    ax.add_collection3d(Poly3DCollection(deck.vectors, facecolors=deck_colors, edgecolors='#4a2200', linewidths=0.04))
    
    stilt_colors = compute_shaded_colors(stilt, np.array([0.38, 0.42, 0.46]))
    ax.add_collection3d(Poly3DCollection(stilt.vectors, facecolors=stilt_colors, edgecolors='#1a1d20', linewidths=0.04))
    
    all_pts = np.vstack([stilt.points.reshape(-1, 3), deck.points.reshape(-1, 3)])
    set_tight_3d_bounds(ax, all_pts, zoom_factor=0.36)
    
    ax.view_init(elev=22, azim=-52)
    ax.set_axis_off()
    
    plt.title("S10 / Sonoma 60/40 Bench Seat Dual Cupholder + Floor Stilt Assembly",
              color='#ffffff', fontsize=14, fontweight='bold', pad=10)
    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', pad_inches=0.02)
    plt.close()
    print(f"Saved: {out_path}")

def render_phone_mount_views(stl_path, out_path):
    print("Rendering Phone Mount CAD Snapshots (Front & Rear)...")
    m_front = mesh.Mesh.from_file(stl_path)
    m_front.rotate([1, 0, 0], np.radians(180))
    m_front.translate(-m_front.min_)
    
    m_rear = mesh.Mesh.from_file(stl_path)
    m_rear.translate(-m_rear.min_)
    
    fig = plt.figure(figsize=(15, 7), dpi=180)
    fig.patch.set_facecolor('#141517')
    
    ax1 = fig.add_subplot(121, projection='3d')
    ax1.set_facecolor('#141517')
    colors1 = compute_shaded_colors(m_front, np.array([0.20, 0.60, 0.88]))
    ax1.add_collection3d(Poly3DCollection(m_front.vectors, facecolors=colors1, edgecolors='#0e2e47', linewidths=0.05))
    set_tight_3d_bounds(ax1, m_front.points.reshape(-1, 3), zoom_factor=0.45)
    ax1.view_init(elev=26, azim=-42)
    ax1.set_axis_off()
    ax1.set_title("Front: 17mm Ball & Dash Faceplate", color='#ffffff', fontsize=12, fontweight='bold', pad=8)
    
    ax2 = fig.add_subplot(122, projection='3d')
    ax2.set_facecolor('#141517')
    colors2 = compute_shaded_colors(m_rear, np.array([0.20, 0.60, 0.88]))
    ax2.add_collection3d(Poly3DCollection(m_rear.vectors, facecolors=colors2, edgecolors='#0e2e47', linewidths=0.05))
    set_tight_3d_bounds(ax2, m_rear.points.reshape(-1, 3), zoom_factor=0.45)
    ax2.view_init(elev=30, azim=135)
    ax2.set_axis_off()
    ax2.set_title("Rear: Factory Bezel Snap Tabs & Recess", color='#ffffff', fontsize=12, fontweight='bold', pad=8)
    
    plt.suptitle("S10 / Sonoma Dashboard Phone Mount (17mm Ball System)", color='#ffffff', fontsize=14, fontweight='bold', y=0.96)
    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', pad_inches=0.02)
    plt.close()
    print(f"Saved: {out_path}")

def render_kit_showcase(deck_stl, stilt_stl, phone_stl, cubby_stl, out_path):
    print("Rendering Complete Kit 3D CAD Showcase...")
    deck = mesh.Mesh.from_file(deck_stl)
    stilt = mesh.Mesh.from_file(stilt_stl)
    phone = mesh.Mesh.from_file(phone_stl)
    cubby = mesh.Mesh.from_file(cubby_stl)
    
    # 1. Assemble cupholder
    stilt.translate([-85.0 / 2, -60.0 / 2, 0])
    deck.translate([0, 0, 290.2])
    
    # 2. Position Phone Mount beside cupholder
    phone.rotate([1, 0, 0], np.radians(180))
    phone.translate(-phone.min_)
    phone.translate([140.0, -30.0, 100.0])
    
    # 3. Position Dash Cubby beside phone mount
    cubby.translate(-cubby.min_)
    cubby.translate([130.0, 70.0, 70.0])
    
    fig = plt.figure(figsize=(15, 9), dpi=180)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#121314')
    fig.patch.set_facecolor('#121314')
    
    c_deck = compute_shaded_colors(deck, np.array([0.94, 0.54, 0.15]))
    ax.add_collection3d(Poly3DCollection(deck.vectors, facecolors=c_deck, edgecolors='#4a2200', linewidths=0.03))
    
    c_stilt = compute_shaded_colors(stilt, np.array([0.38, 0.42, 0.46]))
    ax.add_collection3d(Poly3DCollection(stilt.vectors, facecolors=c_stilt, edgecolors='#1a1d20', linewidths=0.03))
    
    c_phone = compute_shaded_colors(phone, np.array([0.20, 0.60, 0.88]))
    ax.add_collection3d(Poly3DCollection(phone.vectors, facecolors=c_phone, edgecolors='#0e2e47', linewidths=0.04))
    
    c_cubby = compute_shaded_colors(cubby, np.array([0.28, 0.75, 0.52]))
    ax.add_collection3d(Poly3DCollection(cubby.vectors, facecolors=c_cubby, edgecolors='#113824', linewidths=0.04))
    
    all_pts = np.vstack([
        stilt.points.reshape(-1, 3),
        deck.points.reshape(-1, 3),
        phone.points.reshape(-1, 3),
        cubby.points.reshape(-1, 3)
    ])
    set_tight_3d_bounds(ax, all_pts, zoom_factor=0.38)
    
    ax.view_init(elev=24, azim=-48)
    ax.set_axis_off()
    
    plt.title("1994-2004 Chevy S10 & GMC Sonoma 3D Printable Upgrades Kit",
              color='#ffffff', fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', pad_inches=0.02)
    plt.close()
    print(f"Saved: {out_path}")

def main():
    base_dir = r"C:\Users\v-mariorivas\s10-sonoma-3d-prints"
    stls = os.path.join(base_dir, "stls")
    images = os.path.join(base_dir, "images")
    os.makedirs(images, exist_ok=True)
    
    deck_stl = os.path.join(stls, "cupholder", "sonoma_cupholder_deck.stl")
    stilt_stl = os.path.join(stls, "cupholder", "sonoma_glide_stilt.stl")
    cupholder_out = os.path.join(images, "cad_render_cupholder_assembly.png")
    render_cupholder_assembly(deck_stl, stilt_stl, cupholder_out)
    
    phone_stl = os.path.join(stls, "phone_mount", "sonoma_plate_monolithic_ball.stl")
    phone_out = os.path.join(images, "cad_render_phone_mount.png")
    render_phone_mount_views(phone_stl, phone_out)
    
    cubby_stl = os.path.join(stls, "dash_cubby", "S10_glasses_cubby_angled.stl")
    kit_out = os.path.join(images, "cad_render_kit_showcase.png")
    render_kit_showcase(deck_stl, stilt_stl, phone_stl, cubby_stl, kit_out)
    
    print("\nAll 3D CAD model renders complete!")

if __name__ == "__main__":
    main()
