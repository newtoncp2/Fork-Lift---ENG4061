# Robotic Forklift

> **Final Project for ENG4061 - Projeto de Robótica at PUC-Rio.**

This repository contains the documentation, source code, 3D models, and assembly instructions for an autonomous and teleoperated Robotic Forklift. The primary objective of the robot is to safely pick up, transport, and move a palletized payload of up to **0.5 kg** from one shelf to another.

<img width="4284" height="5712" alt="IMG_2752" src="https://github.com/user-attachments/assets/7bc7034e-debe-4b18-bee4-834526973eca" />

## Key Features

The forklift operates in two distinct modes, seamlessly integrating mechanical robustness with advanced control systems:

* **Manual Mode (Teleoperation):** The robot can be manually controlled via a dedicated Web Server. This allows a human operator to drive the robot and operate the forklift mechanism remotely through a browser interface.

* **Autonomous Mode:** The robot is capable of autonomous navigation to move pallets between designated shelves without human intervention.

* **Computer Vision (AprilTags):** In autonomous mode, the robot uses a camera to detect AprilTags placed in the environment (e.g., on shelves or pallets) for precise spatial referencing, localization, and alignment.

* **PID Control:** A custom PID (Proportional-Integral-Derivative) control system ensures smooth, accurate, and stable locomotion when driving and aligning with the target shelves.

## System Architecture

To handle both high-level processing (vision and web server) and low-level hardware control, the system uses a dual-microcontroller architecture.

### Hardware Stack

* **High-Level Processing:** Raspberry Pi 3 (Handles the Web Server, camera input, and AprilTag detection).
* **Low-Level Control:** Arduino (Handles motor drivers, PID calculations, and sensor reading).
* **Locomotion:** 2x LEGO NXT Motors (Used for reliable differential drive locomotion).
* **Lifting Mechanism:** 1x NEMA 17 Stepper Motor paired with 6mm linear guides and LM6UU bearings for the vertical mast.

### Software Stack

* **Computer Vision:** AprilTag recognition pipeline running on the Raspberry Pi.
* **Control Loop:** PID loop running on the Arduino to control the LEGO NXT motors based on target references.
* **Communication:** Serial communication established between the Raspberry Pi (master) and the Arduino (slave).

## Repository Structure

Navigate through the folders below to explore the specific modules of this project:

* `/mechanics` - Contains 3D CAD files (.STEP, .STL) and mechanical documentation.
  * **Read the [Mechanical Assembly & Troubleshooting Guide](mechanics/assembly.md)** for details on the Center of Mass, 3D printing parameters, and structural problem-solving.

* `/src` - Contains all the source code.
  * `/src/arduino` - Low-level motor control and PID implementation.
  * `/src/python` - Web server, AprilTag vision system, and serial communication scripts.

* `/electronics` - Additional schematics, wiring diagrams, and project reports.

*Developed as an academic project for PUC-Rio.
