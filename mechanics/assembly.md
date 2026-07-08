# Mechanical Assembly & Troubleshooting

This document details the mechanical assembly process, structural decisions, and field modifications made to ensure the robotic forklift met the 0.5 kg payload requirement safely and efficiently.

## 1. CAD & 3D Printing Guidelines

All custom parts were designed in Onshape. When printing the structural components (especially the main mast and forks), layer orientation is critical to withstand bending moments.

* **Utilizaed Printer:** Bambu Lab A1
* **Material:** PETG or high-quality PLA (PETG preferred for impact resistance).
* **Infill:** At least 30-40% (Gyroid or Cubic pattern) for the fork and mast components.
* **Orientation:** Print the forks laying flat on the build plate to ensure the layer lines run parallel to the load direction, preventing delamination.

> **Note:** The CAD files (`.STEP` and `.STL`) can be found in the `/cad` folder.

## 2. Base Chassis & Center of Mass

To prevent the forklift from tipping forward when lifting the 0.5 kg payload, the center of gravity (CG) was carefully managed:

* **NEMA 17 Placement:** The NEMA 17 stepper motor is mounted in the geometric center of the chassis. This centralizes the mass and acts as a structural anchor.
* **Counterweight Box:** The elongated blue and orange enclosure (shown in the image below) at the rear of the robot houses the electronics and acts as a physical ballast. This counterweight keeps the CG safely within the wheelbase.

<img width="622" height="730" alt="WhatsApp Image 2026-06-04 at 22 33 42" src="https://github.com/user-attachments/assets/6b752599-96e7-4760-b758-92286f17c3e5" />

## 3. Mast & Linear Motion

The vertical lift system relies on a rigid and smooth linear motion setup. Assembly order is critical here to avoid binding or breaking the 3D printed parts:

* First, press-fit or mount the **6mm linear bearings (LM6UU)** securely into their housings on the fork carriage.
* Insert the **6mm linear guide rods** into the bottom mounts of the main frame.
* Carefully slide the assembled fork carriage (with the pre-installed bearings) down onto the guide rods.
* Finally, cap the top of the mast to lock the rods in place, ensuring they are perfectly parallel to prevent binding during manual operation.

## 4. Safety Interlock System

Since the forklift operates via manual open-loop control, a hardware safety measure was implemented to prevent structural damage.
* **Endstop Switch:** Mount the tactile limit switch at the very top of the mast.
* **Function:** This acts as a mechanical interlock. If the operator attempts to raise the fork beyond the maximum height, the fork triggers the switch, instantly cutting power to the NEMA 17 motor.

## 5. Field Modifications & Troubleshooting

During physical testing, the gap between theoretical CAD and the real world required a few immediate engineering solutions:

### A. Load Slipping (Friction Issue)
* **Problem:** The 3D printed surface of the forks was too smooth, causing the pallet to slide off during movement.
* **Solution:** Drops of hot glue were strategically applied to specific contact points on the forks. This significantly increased the static friction coefficient, locking the pallet in place.

### B. Frame Bending (Structural Rigidity)
* **Problem:** The frame holding the linear guides only had three support points. Under load, the structure would yield and tilt upward.
* **Solution:** Instead of redesigning and enlargening the structure, holes were designed into the frame and tensioned ropes were attached. These ropes act as tensile trusses, rigidifying the entire mast assembly and eliminating the tilt.

### C. Z-Axis Tolerance (Shelf Clearance)
* **Problem:** The maximum Z-height of the forks was designed with very tight tolerances. When fully loaded, it struggled to clear the shelf height for pallet placement.
* **Solution:** Two custom extension attachments were designed and 3D printed. These snap onto the existing forks, providing the extra Z-height clearance needed for smooth operation without modifying the main mast.
