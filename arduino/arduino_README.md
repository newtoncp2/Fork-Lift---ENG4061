# Arduino Low-Level Control (Firmware)

This directory contains the firmware for the Arduino MEGA 2560, which acts as the low-level hardware controller (Slave) in the master-slave architecture. 

While the Raspberry Pi handles computer vision and path planning, this Arduino is strictly responsible for real-time operations: executing the PID control loop for locomotion, driving the NEMA 17 stepper motor, reading quadrature encoders via hardware interrupts, and polling telemetry sensors.

## Dependencies

To compile and upload this code, you must install the following libraries via the Arduino IDE Library Manager:
* **`Encoder`** (by Paul Stoffregen) - For high-speed hardware interrupt encoder reading.
* **`Adafruit_INA219`** - For polling the voltage and current sensor.
* **`ArduinoJson`** (v6 or v7) - For serializing telemetry data into JSON format.

## Operating Modes & Serial Protocol

The Arduino receives commands from the Raspberry Pi via Serial communication (Baud Rate: 115200). The command string is formatted as `<MODE> <PARAM1>,<PARAM2>\n`.

The firmware processes 4 distinct operational modes:

| Mode | Type | Syntax Example | Description |
| :--- | :--- | :--- | :--- |
| **`0`** | **Manual (Teleoperation)** | `0 100,-100\n` | Expects target RPMs for the Left and Right motors, respectively. Used for manual joystick control. |
| **`1`** | **Autonomous (Rotate)** | `1 1.57\n` | Expects a target angle `theta` (in radians). Calculates the required encoder pulses and applies opposite RPMs to pivot the robot in place. |
| **`2`** | **Autonomous (Forward)** | `2 0.5\n` | Expects a target distance `rho` (in meters). Calculates the required encoder pulses and applies equal RPMs to drive straight. |
| **`3`** | **Forklift Mast** | `3 50\n` | Expects a target position percentage (-100 to 100). Translates the percentage into stepper pulses using the `KS` (Step Gain) multiplier. |

> **Note on Autonomous Callbacks:** In modes 1 and 2, once the target number of encoder pulses is reached, the Arduino automatically stops the motors and sends a `fim modo X` string back to the Raspberry Pi to advance the higher-level State Machine.

## Control System Architecture

### 1. Locomotion Kinematics
The code uses hardcoded physical measurements of the robot to translate high-level spatial commands (radians and meters) into wheel rotations:
* **Wheelbase (`L`):** 0.195 meters.
* **Wheel Radius (`R`):** 0.027 meters.
* **Max RPM:** Capped at 150 RPM to ensure torque stability.

### 2. PID Control Loop
The main loop executes a closed-loop PID controller every `Ts` (20 milliseconds). 
* It calculates the current RPM of each wheel using the hardware encoders.
* Compares it to the target RPM to generate an error value.
* Applies Proportional (`KP`), Integral (`KI`), and Derivative (`KD`) gains to adjust the PWM output sent to the L298N driver. *(Note: KI and KD are currently zeroed out, relying on purely Proportional tuning `0.7 * KU`)*.

## Hardware Safety Features

The firmware includes several safety constraints to protect both the robot's structure and its electronics:

1. **Stepper Motor Fault Detection (`FLT` Pin):**
   If the DRV8825 driver detects a thermal shutdown or overcurrent event, it pulls the `FLT` pin LOW. The Arduino immediately intercepts this, stops the drive motors (ENA and ENB to 0), and disables the stepper driver.
2. **Mast Endstop Interlock (`B2` Pin):**
   During Mode 3 (Mast operation), the firmware continuously checks the tactile button at the top of the mast. If the button is triggered (`LOW`) while the motor direction is set to UP, the stepping loop is instantly aborted to prevent the 3D-printed carriage from crashing into the frame.
3. **Battery Undervoltage Protection:**
   The INA219 sensor is polled periodically. If the bus voltage drops below **9.7V**, the Arduino sends a "shutdown command" warning over Serial to prevent deep-discharging and permanently damaging the 3S Li-ion battery pack.
