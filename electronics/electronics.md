# Electronics & Wiring Architecture

This document outlines the hardware architecture, power distribution, and telemetry sensors used in the Robotic Forklift. The system relies on a dual-microcontroller setup to separate high-level computational tasks from low-level real-time hardware control.

## 1. Microcontrollers & Communication

The core of the robot operates on a Master-Slave architecture:
* **Raspberry Pi 3 (Master):** Handles the web server, WebSocket video streaming, and AprilTag computer vision processing. Operates at 3.3V logic.
* **Arduino MEGA 2560 (Slave):** Handles real-time PID motor control, stepper pulses, and sensor polling. Operates at 5V logic.
* **Logic Level Shifter (4CH):** Essential for safe Serial communication (TX/RX) between the Raspberry Pi and the Arduino, stepping the 3.3V signals up to 5V and vice versa to prevent pin damage.

## 2. Power Management

The robot is powered by an autonomous battery system, stepped down to meet the specific requirements of each component:
* **Power Source:** A 3S 18650 Li-ion battery pack (nominally 11.1V, up to 12.6V fully charged).
* **BMS (Battery Management System):** An HX-3S-FL10 module ensures safe charging/discharging and cell balancing.
* **Voltage Regulation:**
  * **U12 (XL4015 Buck Converter):** Steps down the battery voltage to a stable **5V** to power the Raspberry Pi 3 via Micro USB.
  * **U10 (XL4015 Buck Converter):** Steps down the battery voltage to a safe level (typically 7V-9V) to power the Arduino Mega via the P4 Barrel Jack.

## 3. Motor Drivers & Actuators

* **Locomotion (NXT Motors):** Driven by an **L298N** Dual H-Bridge motor driver. It takes PWM signals from the Arduino to control the speed and direction of the differential drive system.
* **Forklift Mast (NEMA 17):** Driven by a **DRV8825** stepper motor driver. Configured with a 47uF decoupling capacitor on the VMOT line to protect against voltage spikes. The `DIR` and `STEP` pins are controlled directly by the Arduino.

## 4. Telemetry & Sensors

To feed the Grafana Dashboard with real-time health data, the system includes dedicated monitoring hardware:
* **INA219 (Voltage & Current Sensor):** Connected via I2C (`SCL`/`SDA`) to the Arduino Mega. It measures the real-time current draw and voltage of the battery pack, allowing the calculation of the overall power consumption (mW).
