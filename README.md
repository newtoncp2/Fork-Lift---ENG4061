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

* **Concurrency:** The Raspberry Pi script uses a mix of `threading` (for blocking serial reads/writes) and `asyncio` (for WebSocket streaming) with thread-safe queues.
* **Computer Vision:** OpenCV and AprilTag pipeline.
* **Communication Protocol:** * MQTT (with TLS encryption) to handle telemetry and command payloads.
  * WebSockets (`websockets` library) to stream real-time video feed frames directly to the Flask dashboard.
  * Serial Communication to relay movement commands to the Arduino.
 
## Telemetry & Monitoring (Grafana)

To monitor the robot's health and performance in real-time, a telemetry pipeline was built using a **PostgreSQL** database and a **Grafana** dashboard. 

This setup allows operators to track critical system metrics during both manual and autonomous operations:
* **Power Consumption:** Real-time monitoring of Voltage (V), Current (mA), and overall Power (mW).
* **Locomotion:** Live RPM tracking for both the left and right LEGO NXT motors.
* **System Status:** Live display of the current operational state (Manual, Autonomous, Search, Aligning) and immediate alerts for Stepper Motor failures.

<img width="1286" height="527" alt="Screenshot 2026-07-08 175515" src="https://github.com/user-attachments/assets/1c688248-5880-47ad-ac23-02510c81d587" />

> **Import the Dashboard:** The raw JSON template for this dashboard is available in [`telemetry/telemetry_grafana.json`](telemetry/rb_telemetria.json). You can import it directly into your own Grafana instance to replicate this monitoring setup.

## Repository Structure

Navigate through the folders below to explore the specific modules of this project:

* `/mechanics` - Contains 3D CAD files (.STEP, .STL) and mechanical documentation.
  * **Read the [Mechanical Assembly & Troubleshooting Guide](mechanics/assembly.md)** for details on the Center of Mass, 3D printing parameters, and structural problem-solving.

* `/src` - Contains all the source code.
  * `/src/arduino` - Low-level motor control and PID implementation.
  * `/src/python/raspberry_pi` - Web server, AprilTag vision system, and serial communication scripts.
  * `/src/python/server` - Flask web server and MQTT broker configuration.
* `/electronics` - Additional schematics, wiring diagrams, and project reports.
* `/telemetry` - Contains the Grafana dashboard JSON template.

*Developed as an academic project for PUC-Rio.
