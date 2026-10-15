#!/usr/bin/env python3
"""
Production-Grade Smooth Phong CAD Studio Renderer for STL Models.
- Computes accurate unit face normals from triangle vertices (cross products).
- Auto-crease smoothing (35 degree threshold) so spheres, cylinders, and fillets
  are 100% round and silky smooth, while edges and flat faces remain crisp.
- Specular highlights and balanced 3-point studio lighting.
- Studio presentation with level, natural perspectives.
"""

import os, time
import numpy as np
from stl import mesh
from PIL import Image

def compute_accurate_normals(v0, v1, v2):
    cross = np.cross(v1 - v0, v2 - v0)
    lens = np.linalg.norm(cross, axis=1, keepdims=True)
    return cross / np.maximum(lens, 1e-8)

def compute_crease_smooth_normals(v0, v1, v2, fn, is_part_id=None, crease_deg=35.0):
    n_tri = len(v0)
    all_verts = np.vstack([v0, v1, v2])
    unq_verts, inverse = np.unique(np.round(all_verts, 3), axis=0, return_inverse=True)
    tri_vert_indices = np.column_stack([inverse[:n_tri], inverse[n_tri:2*n_tri], inverse[2*n_tri:]])

    vert_to_tris = [[] for _ in range(len(unq_verts))]
    for t_i in range(n_tri):
        for k in range(3):
            vert_to_tris[tri_vert_indices[t_i, k]].append(t_i)

    cos_crease = np.cos(np.radians(crease_deg))
    tri_vert_normals = np.zeros((n_tri, 3, 3), dtype=np.float32)

    for t_i in range(n_tri):
        fn_i = fn[t_i]
        p_id = is_part_id[t_i] if is_part_id is not None else 0
        for k in range(3):
            v_idx = tri_vert_indices[t_i, k]
            neighbor_tris = vert_to_tris[v_idx]
            acc_n = np.zeros(3, dtype=np.float32)
            for nb in neighbor_tris:
                nb_p_id = is_part_id[nb] if is_part_id is not None else 0
                if nb_p_id == p_id and np.dot(fn_i, fn[nb]) >= cos_crease:
                    acc_n += fn[nb]
            norm = np.linalg.norm(acc_n)
            tri_vert_normals[t_i, k] = acc_n / norm if norm > 0 else fn_i

    return tri_vert_normals

def render_mesh_studio(v0, v1, v2, colors, W=1200, H=900,
                       elev_deg=20, azim_deg=0, roll_deg=0,
                       zoom_factor=0.72, is_part_id=None,
                       bg_color=(238, 240, 244),
                       crease_deg=35.0):
    all_pts = np.vstack([v0, v1, v2])
    center = np.mean(all_pts, axis=0)
    scale = np.max(np.ptp(all_pts, axis=0))

    fn = compute_accurate_normals(v0, v1, v2)

    el = np.radians(elev_deg)
    az = np.radians(azim_deg)
    ro = np.radians(roll_deg)
    
    R_az = np.array([[np.cos(az), -np.sin(az), 0],
                     [np.sin(az),  np.cos(az), 0],
                     [0,           0,          1]], dtype=np.float32)
    R_el = np.array([[1, 0,           0],
                     [0, np.cos(el), -np.sin(el)],
                     [0, np.sin(el),  np.cos(el)]], dtype=np.float32)
    R_ro = np.array([[np.cos(ro), -np.sin(ro), 0],
                     [np.sin(ro),  np.cos(ro), 0],
                     [0,           0,          1]], dtype=np.float32)
    R = R_ro @ (R_el @ R_az)

    v0_c = (v0 - center) @ R.T
    v1_c = (v1 - center) @ R.T
    v2_c = (v2 - center) @ R.T

    zoom = zoom_factor * min(W, H) / scale
    p0 = v0_c[:, :2] * zoom + np.array([W / 2.0, H / 2.0])
    p1 = v1_c[:, :2] * zoom + np.array([W / 2.0, H / 2.0])
    p2 = v2_c[:, :2] * zoom + np.array([W / 2.0, H / 2.0])
    p0[:, 1] = H - p0[:, 1]
    p1[:, 1] = H - p1[:, 1]
    p2[:, 1] = H - p2[:, 1]

    z0, z1, z2 = v0_c[:, 2], v1_c[:, 2], v2_c[:, 2]

    cross2d = (p1[:, 0] - p0[:, 0]) * (p2[:, 1] - p0[:, 1]) - (p1[:, 1] - p0[:, 1]) * (p2[:, 0] - p0[:, 0])
    front = cross2d < 0
    idx = np.where(front)[0]

    tv_normals = compute_crease_smooth_normals(v0, v1, v2, fn, is_part_id, crease_deg)
    vn0 = tv_normals[:, 0] @ R.T
    vn1 = tv_normals[:, 1] @ R.T
    vn2 = tv_normals[:, 2] @ R.T

    key_light = np.array([0.40, -0.55, 0.75], dtype=np.float32)
    key_light /= np.linalg.norm(key_light)
    fill_light = np.array([-0.50, 0.40, 0.45], dtype=np.float32)
    fill_light /= np.linalg.norm(fill_light)
    rim_light = np.array([0.0, 0.85, 0.20], dtype=np.float32)
    rim_light /= np.linalg.norm(rim_light)

    view_dir = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    half_vec = (key_light + view_dir) / np.linalg.norm(key_light + view_dir)

    def compute_lighting(vn, base_rgb):
        diff_key = np.maximum(0, np.sum(vn * key_light, axis=-1, keepdims=True))
        diff_fill = np.maximum(0, np.sum(vn * fill_light, axis=-1, keepdims=True))
        diff_rim = np.maximum(0, np.sum(vn * rim_light, axis=-1, keepdims=True))
        spec = np.maximum(0, np.sum(vn * half_vec, axis=-1, keepdims=True)) ** 24

        lit = (0.34 * base_rgb +
               0.50 * diff_key * base_rgb +
               0.18 * diff_fill * base_rgb +
               0.08 * diff_rim * base_rgb +
               0.32 * spec * 255.0)
        return np.clip(lit, 0, 255).astype(np.float32)

    c0 = compute_lighting(vn0, colors)
    c1 = compute_lighting(vn1, colors)
    c2 = compute_lighting(vn2, colors)

    img = np.full((H, W, 3), bg_color, dtype=np.uint8)
    zbuf = np.full((H, W), -1e9, dtype=np.float32)

    for i in idx:
        x_min = max(0, int(np.floor(min(p0[i, 0], p1[i, 0], p2[i, 0]))))
        x_max = min(W - 1, int(np.ceil(max(p0[i, 0], p1[i, 0], p2[i, 0]))))
        y_min = max(0, int(np.floor(min(p0[i, 1], p1[i, 1], p2[i, 1]))))
        y_max = min(H - 1, int(np.ceil(max(p0[i, 1], p1[i, 1], p2[i, 1]))))
        if x_max < x_min or y_max < y_min:
            continue

        denom = cross2d[i]
        xs = np.arange(x_min, x_max + 1)
        ys = np.arange(y_min, y_max + 1)
        X, Y = np.meshgrid(xs, ys)

        w0 = ((p2[i, 0] - p1[i, 0]) * (Y - p1[i, 1]) - (p2[i, 1] - p1[i, 1]) * (X - p1[i, 0])) / denom
        w1 = ((p0[i, 0] - p2[i, 0]) * (Y - p2[i, 1]) - (p0[i, 1] - p2[i, 1]) * (X - p2[i, 0])) / denom
        w2 = 1.0 - w0 - w1

        mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not np.any(mask):
            continue

        z = w0 * z0[i] + w1 * z1[i] + w2 * z2[i]
        z_mask = mask & (z > zbuf[y_min:y_max+1, x_min:x_max+1])
        if not np.any(z_mask):
            continue

        cur_zbuf = zbuf[y_min:y_max+1, x_min:x_max+1]
        cur_zbuf[z_mask] = z[z_mask]

        pix_c = (w0[..., None] * c0[i] + w1[..., None] * c1[i] + w2[..., None] * c2[i])
        cur_img = img[y_min:y_max+1, x_min:x_max+1]
        cur_img[z_mask] = pix_c[z_mask].astype(np.uint8)

    return Image.fromarray(img)

def render_smooth_phone_mount(stl_path, out_path):
    print("Rendering Smooth Phone Mount Dual CAD Views...")
    m_front = mesh.Mesh.from_file(stl_path)
    # Rotate -90 around X so faceplate stands upright in XZ plane, ball points forward along +Y
    m_front.rotate([1, 0, 0], np.radians(-90))
    m_front.translate(-m_front.min_)

    m_rear = mesh.Mesh.from_file(stl_path)
    # Rotate +90 around X so rear clips face forward along +Y
    m_rear.rotate([1, 0, 0], np.radians(90))
    m_rear.translate(-m_rear.min_)

    base_front = np.full((len(m_front.v0), 3), [54, 58, 66], dtype=np.float32)
    base_rear = np.full((len(m_rear.v0), 3), [54, 58, 66], dtype=np.float32)

    # Front 3/4 view
    img_front = render_mesh_studio(
        m_front.v0, m_front.v1, m_front.v2, base_front,
        W=750, H=800, elev_deg=18, azim_deg=-20, roll_deg=0,
        zoom_factor=0.62, crease_deg=35.0
    )

    # Rear 3/4 view showing clips
    img_rear = render_mesh_studio(
        m_rear.v0, m_rear.v1, m_rear.v2, base_rear,
        W=750, H=800, elev_deg=18, azim_deg=20, roll_deg=0,
        zoom_factor=0.62, crease_deg=35.0
    )

    dual = Image.new("RGB", (1500, 800), (238, 240, 244))
    dual.paste(img_front, (0, 0))
    dual.paste(img_rear, (750, 0))
    dual.save(out_path)
    print(f"Saved: {out_path}")

def render_smooth_cupholder(deck_path, stilt_path, out_path):
    print("Rendering Smooth Cupholder Assembly CAD...")
    deck = mesh.Mesh.from_file(deck_path)
    stilt = mesh.Mesh.from_file(stilt_path)

    stilt.translate([-85.0 / 2, -60.0 / 2, 0])
    deck.translate([0, 0, 290.2])

    v0 = np.vstack([deck.v0, stilt.v0])
    v1 = np.vstack([deck.v1, stilt.v1])
    v2 = np.vstack([deck.v2, stilt.v2])

    part_id = np.zeros(len(v0), dtype=np.int32)
    part_id[len(deck.v0):] = 1

    colors = np.zeros((len(v0), 3), dtype=np.float32)
    colors[:len(deck.v0)] = [56, 60, 68]
    colors[len(deck.v0):] = [40, 42, 46]

    # Front 3/4 angle with 15 deg turn for depth
    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1200, H=1000, elev_deg=22, azim_deg=15, roll_deg=0,
        zoom_factor=0.70, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

def render_smooth_magnetic_cubby(dock_path, stealth_path, magsafe_path, ball_path, out_path):
    print("Rendering Smooth Modular Magnetic Cubby Ecosystem CAD...")
    dock = mesh.Mesh.from_file(dock_path)
    stealth = mesh.Mesh.from_file(stealth_path)
    magsafe = mesh.Mesh.from_file(magsafe_path)
    ball = mesh.Mesh.from_file(ball_path)

    dock.rotate([0, 1, 0], np.radians(180))
    dock.rotate([1, 0, 0], np.radians(70))
    dock.rotate([0, 0, 1], np.radians(-25))

    for p in [stealth, magsafe, ball]:
        p.rotate([1, 0, 0], np.radians(-110))
        p.rotate([0, 0, 1], np.radians(-10))

    parts = [dock, stealth, magsafe, ball]
    xs = [-130.0, -42.0, 40.0, 122.0]
    for p, target_x in zip(parts, xs):
        c = np.mean(np.vstack([p.v0, p.v1, p.v2]), axis=0)
        p.translate([-c[0] + target_x, -c[1], -c[2]])

    v0 = np.vstack([dock.v0, stealth.v0, magsafe.v0, ball.v0])
    v1 = np.vstack([dock.v1, stealth.v1, magsafe.v1, ball.v1])
    v2 = np.vstack([dock.v2, stealth.v2, magsafe.v2, ball.v2])

    part_id = np.zeros(len(v0), dtype=np.int32)
    i1 = len(dock.v0)
    i2 = i1 + len(stealth.v0)
    i3 = i2 + len(magsafe.v0)
    part_id[i1:i2] = 1
    part_id[i2:i3] = 2
    part_id[i3:] = 3

    colors = np.zeros((len(v0), 3), dtype=np.float32)
    colors[:i1] = [52, 56, 64]      # Dock: Matte Anthracite
    colors[i1:i2] = [38, 40, 46]    # Stealth Cover: Gunmetal Stealth
    colors[i2:i3] = [45, 95, 145]   # MagSafe: Tech Blue
    colors[i3:] = [55, 115, 95]     # Ball: Forest Sage

    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1600, H=700, elev_deg=18, azim_deg=0, roll_deg=0,
        zoom_factor=1.12, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

def render_smooth_cubby_slide(dock_path, cartridge_path, combo_path, out_path):
    print("Rendering Smooth Slide & Combo Cubby CAD...")
    slide_dock = mesh.Mesh.from_file(dock_path)
    cartridge = mesh.Mesh.from_file(cartridge_path)
    combo = mesh.Mesh.from_file(combo_path)

    slide_dock.rotate([0, 1, 0], np.radians(180))
    slide_dock.rotate([1, 0, 0], np.radians(70))
    slide_dock.rotate([0, 0, 1], np.radians(-25))

    cartridge.rotate([1, 0, 0], np.radians(-110))
    cartridge.rotate([0, 0, 1], np.radians(-20))

    combo.rotate([0, 1, 0], np.radians(180))
    combo.rotate([1, 0, 0], np.radians(70))
    combo.rotate([0, 0, 1], np.radians(-25))

    parts = [slide_dock, cartridge, combo]
    xs = [-95.0, -10.0, 95.0]
    for p, target_x in zip(parts, xs):
        c = np.mean(np.vstack([p.v0, p.v1, p.v2]), axis=0)
        p.translate([-c[0] + target_x, -c[1], -c[2]])

    v0 = np.vstack([slide_dock.v0, cartridge.v0, combo.v0])
    v1 = np.vstack([slide_dock.v1, cartridge.v1, combo.v1])
    v2 = np.vstack([slide_dock.v2, cartridge.v2, combo.v2])

    part_id = np.zeros(len(v0), dtype=np.int32)
    i1 = len(slide_dock.v0)
    i2 = i1 + len(cartridge.v0)
    part_id[i1:i2] = 1
    part_id[i2:] = 2

    colors = np.zeros((len(v0), 3), dtype=np.float32)
    colors[:i1] = [52, 56, 64]      # Slide Dock: Matte Anthracite
    colors[i1:i2] = [45, 95, 145]   # Cartridge: Tech Blue
    colors[i2:] = [48, 110, 85]     # 2-in-1 Combo: Slate Green

    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1600, H=800, elev_deg=18, azim_deg=0, roll_deg=0,
        zoom_factor=0.98, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

def render_smooth_kit_showcase(deck_path, stilt_path, phone_path, cubby_path, stealth_path, out_path):
    print("Rendering Smooth Complete Kit CAD Showcase...")
    deck = mesh.Mesh.from_file(deck_path)
    stilt = mesh.Mesh.from_file(stilt_path)
    phone = mesh.Mesh.from_file(phone_path)
    cubby = mesh.Mesh.from_file(cubby_path)
    stealth = mesh.Mesh.from_file(stealth_path)

    stilt.translate([-85.0 / 2, -60.0 / 2, 0])
    deck.translate([0, 0, 290.2])

    # Upright phone mount
    phone.rotate([1, 0, 0], np.radians(-90))
    phone.translate(-phone.min_)
    phone.translate([130.0, -20.0, 80.0])

    # Cubby dock
    cubby.rotate([0, 1, 0], np.radians(180))
    cubby.rotate([1, 0, 0], np.radians(70))
    cubby.rotate([0, 0, 1], np.radians(-25))
    cubby.translate(-cubby.min_)
    cubby.translate([135.0, 80.0, 60.0])

    # Stealth cover hovering next to cubby
    stealth.rotate([1, 0, 0], np.radians(-110))
    stealth.rotate([0, 0, 1], np.radians(-10))
    stealth.translate(-stealth.min_)
    stealth.translate([145.0, 140.0, 120.0])

    v0 = np.vstack([deck.v0, stilt.v0, phone.v0, cubby.v0, stealth.v0])
    v1 = np.vstack([deck.v1, stilt.v1, phone.v1, cubby.v1, stealth.v1])
    v2 = np.vstack([deck.v2, stilt.v2, phone.v2, cubby.v2, stealth.v2])

    part_id = np.zeros(len(v0), dtype=np.int32)
    i1 = len(deck.v0)
    i2 = i1 + len(stilt.v0)
    i3 = i2 + len(phone.v0)
    i4 = i3 + len(cubby.v0)
    part_id[i1:i2] = 1
    part_id[i2:i3] = 2
    part_id[i3:i4] = 3
    part_id[i4:] = 4

    colors = np.zeros((len(v0), 3), dtype=np.float32)
    colors[:i1] = [56, 60, 68]       # Deck: Matte Anthracite
    colors[i1:i2] = [40, 42, 46]   # Stilt: Textured Black
    colors[i2:i3] = [48, 95, 145]  # Phone Mount: Steel Blue
    colors[i3:i4] = [52, 56, 64]   # Cubby Dock: Matte Anthracite
    colors[i4:] = [38, 40, 46]     # Stealth Cover: Gunmetal Stealth

    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1600, H=1000, elev_deg=22, azim_deg=15, roll_deg=0,
        zoom_factor=0.72, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

def render_smooth_ashtray_mods(usb_path, deep_path, combo_path, out_path):
    print("Rendering Smooth Ashtray Mods CAD...")
    usb_p = mesh.Mesh.from_file(usb_path)
    deep_p = mesh.Mesh.from_file(deep_path)
    combo_p = mesh.Mesh.from_file(combo_path)

    # Orientation: face upright and tilt back 20 deg
    for p in [usb_p, deep_p, combo_p]:
        p.rotate([1, 0, 0], np.radians(-110))
        p.rotate([0, 0, 1], np.radians(-10))

    parts = [usb_p, combo_p, deep_p]
    xs = [-105.0, 0.0, 105.0]
    for p, target_x in zip(parts, xs):
        c = np.mean(np.vstack([p.v0, p.v1, p.v2]), axis=0)
        p.translate([-c[0] + target_x, -c[1], -c[2]])

    v0 = np.vstack([usb_p.v0, combo_p.v0, deep_p.v0])
    v1 = np.vstack([usb_p.v1, combo_p.v1, deep_p.v1])
    v2 = np.vstack([usb_p.v2, combo_p.v2, deep_p.v2])

    part_id = np.zeros(len(v0), dtype=np.int32)
    i1 = len(usb_p.v0)
    i2 = i1 + len(combo_p.v0)
    part_id[i1:i2] = 1
    part_id[i2:] = 2

    colors = np.zeros((len(v0), 3), dtype=np.float32)
    colors[:i1] = [45, 95, 145]    # USB Panel: Tech Blue
    colors[i1:i2] = [48, 110, 85]  # Combo: Slate Green
    colors[i2:] = [52, 56, 64]     # Deep Pocket: Anthracite

    img = render_mesh_studio(
        v0, v1, v2, colors,
        W=1600, H=800, elev_deg=18, azim_deg=0, roll_deg=0,
        zoom_factor=1.05, is_part_id=part_id, crease_deg=35.0
    )
    img.save(out_path)
    print(f"Saved: {out_path}")

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stls = os.path.join(base, "stls")
    imgs = os.path.join(base, "images")
    os.makedirs(imgs, exist_ok=True)

    deck_stl = os.path.join(stls, "cupholder", "sonoma_cupholder_deck.stl")
    stilt_stl = os.path.join(stls, "cupholder", "sonoma_glide_stilt.stl")
    phone_stl = os.path.join(stls, "phone_mount", "sonoma_plate_monolithic_ball.stl")
    cubby_mag_stl = os.path.join(stls, "dash_cubby", "S10_cubby_magnetic_dock.stl")
    cubby_stealth_stl = os.path.join(stls, "dash_cubby", "S10_cubby_mag_stealth_cover.stl")
    cubby_magsafe_stl = os.path.join(stls, "dash_cubby", "S10_cubby_mag_magsafe_plate.stl")
    cubby_ball_stl = os.path.join(stls, "dash_cubby", "S10_cubby_mag_ball_plate.stl")
    
    ashtray_usb_stl = os.path.join(stls, "ashtray", "S10_ashtray_usb_power_panel.stl")
    ashtray_deep_stl = os.path.join(stls, "ashtray", "S10_ashtray_deep_pocket.stl")
    ashtray_combo_stl = os.path.join(stls, "ashtray", "S10_ashtray_combo_power_pocket.stl")

    render_smooth_phone_mount(phone_stl, os.path.join(imgs, "cad_render_phone_mount.png"))
    render_smooth_cupholder(deck_stl, stilt_stl, os.path.join(imgs, "cad_render_cupholder_assembly.png"))
    render_smooth_magnetic_cubby(cubby_mag_stl, cubby_stealth_stl, cubby_magsafe_stl, cubby_ball_stl,
                                 os.path.join(imgs, "cad_render_cubby_magnetic.png"))
    render_smooth_ashtray_mods(ashtray_usb_stl, ashtray_deep_stl, ashtray_combo_stl,
                               os.path.join(imgs, "cad_render_ashtray_mods.png"))
    render_smooth_kit_showcase(deck_stl, stilt_stl, phone_stl, cubby_mag_stl, cubby_stealth_stl,
                               os.path.join(imgs, "cad_render_kit_showcase.png"))

if __name__ == "__main__":
    main()
