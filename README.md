# 1994–2004 Chevy S10 & GMC Sonoma 3D Printed Accessories

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![3D Print Ready](https://img.shields.io/badge/Format-STL%20%7C%20CAD-orange.svg)]()

A complete collection of custom, functional 3D printable upgrades designed specifically for **1994–2004 Chevrolet S10, GMC Sonoma, S10 Blazer, GMC Jimmy, and Oldsmobile Bravada** trucks and SUVs.

<p align="center">
  <img src="images/cad_render_kit_showcase.png" width="100%" alt="Chevy S10 / GMC Sonoma 3D Printed Accessories Kit" />
</p>
<p align="center">
  <img src="images/cad_render_cupholder_assembly.png" width="49%" alt="Bench Seat Cupholder CAD Assembly" />
  <img src="images/cad_render_phone_mount.png" width="49%" alt="Dashboard Phone Mount Front and Rear CAD Views" />
</p>

---

## 🚗 Vehicle Compatibility

* **1994–2004 Chevrolet S10** (Regular Cab, Extended Cab, Crew Cab)
* **1994–2004 GMC Sonoma**
* **1995–2005 Chevrolet Blazer / S10 Blazer**
* **1995–2001 GMC Jimmy**
* **1996–2001 Oldsmobile Bravada**

---

## 📦 What's Included

### 1. Dashboard Phone Mount System (17mm Ball / MagSafe / Garmin)
Located in [`stls/phone_mount/`](stls/phone_mount/)

Designed to replace the factory blanking plate / switch bezel on the dashboard to the right of the instrument cluster:

* **`sonoma_plate_monolithic_ball.stl` & `sonoma_plate_monolithic_symmetrical.stl`**:
  * **Zero Hardware Needed.** Fuses the OEM snap plate and a 17mm ball mount into a single monolithic print.
* **`sonoma_plate_metal_ball.stl` & `sonoma_plate_metal_ball_symmetrical.stl`**:
  * Designed for heavy-duty metal 17mm ball studs with a standard **1/4"-20 threaded post**.
  * Features a molded rear captive hex-nut pocket (11.5mm flats, 6mm depth) inside the reinforced boss.
* **`sonoma_plate_printed_ball.stl` & `ball_17mm_frontmount.stl`**:
  * **Front-Serviceable 2-Piece System.** Uses two front-mounted counter-bored M3 / #6 screws with captive rear nuts.
  * Allows swapping or servicing ball mounts without removing the dashboard trim bezel!

---

### 2. Dual Stepped Bench Seat Cupholder (Large Bottle & Stanley Mug)
Located in [`stls/cupholder/`](stls/cupholder/)

Solves the infamous lack of functional cupholders in 90s GM bench seat trucks:

* **`sonoma_cupholder_deck.stl`**:
  * Slides into the factory center bench seat receiver slot with a positive retention catch bump.
  * **Triple-stepped bore** holds everything from standard 12oz soda cans (2.75" bottom pocket) to Stanley 30oz/40oz tumblers, Hydro Flasks, and YETI 35oz mugs.
  * Outward-facing handle clearance notches for large travel mugs.
* **`sonoma_glide_stilt.stl`**:
  * Heavy-duty ribbed compression stilt leg that presses into the keyed socket beneath the deck.
  * Features a curved glide foot contoured to the factory transmission tunnel hump, keeping drinks completely level and rock solid under heavy braking.
  * Includes a recessed pocket on the bottom for a 1.5" felt or rubber pad to protect carpet.

---

### 3. Dash Cubby Organizers
Located in [`stls/dash_cubby/`](stls/dash_cubby/)

Replaces open factory dash dash pockets with functional storage:
* **`S10_glasses_cubby_angled.stl`**: Angled sunglasses/phone tray.
* **`S10_glasses_cubby_deep.stl`**: Deep storage cubby.
* **`S10_dash_cubby.stl`**: OEM profile replacement insert.

---

## 🖨️ Recommended Print Settings

> [!IMPORTANT]
> **Material Warning:** Because car interiors in the summer can easily exceed **60°C to 70°C (140°F – 160°F)**, **DO NOT USE STANDARD PLA**! PLA will deform, soften, and warp in hot vehicles.

* **Recommended Filament:** **PETG**, **ABS**, or **ASA** (ASA is ideal for UV and heat resistance).
* **Layer Height:** `0.20mm` (or `0.16mm` for ball studs).
* **Perimeters / Walls:** `4 to 5 walls` (Crucial for mechanical strength on phone ball stems and seat tongues).
* **Infill:** `30% to 45%` (Gyroid or Grid).
* **Supports:**
  * Phone plates: Print flat face-down on build plate. Supports required only under the rear snap tabs.
  * Ball stud (`ball_17mm_frontmount.stl`): Print oriented on its flat side for maximum layer adhesion strength along the stem axis.
  * Cupholder deck: Print right-side up with tree supports under the tongue.

---

## 💻 Parametric CAD Source Code

All parts were programmatically designed in Python using the modern `manifold3d` geometric modeling engine. Source scripts are in [`src/`](src/):
* `src/generate_all_phone_mounts.py`: Parametric phone mount generator.
* `src/generate_sonoma_cupholder.py`: Bench cupholder and stilt generator.
* `src/export_symmetrical_mounts.py`: Symmetrical plate exports.

You can modify cup diameters, stilt drop heights, or ball tilt angles directly in the Python scripts!

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free to print, modify, and share.
