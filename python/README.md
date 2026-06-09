# Fork-Lift AprilTag Detection (Python)

## Overview
This project provides a local WebRTC-based architecture for real-time video streaming and AprilTag detection. It captures webcam video on a client (e.g., a Raspberry Pi), streams it over WebRTC to a backend receiver, and performs pose estimation on detected AprilTags. 

For every detected tag, the script prints coordinates to the console in the format:
`id, x, y, z, pitch`

## Project Structure

*   **`raspberry.py`**
    WebRTC offerer. Captures the webcam video stream and sends it via WebRTC to the backend receiver.
*   **`video_processor.py`** (formerly `backend.py` or `test.py`)
    WebRTC answerer. Receives the stream, processes it with OpenCV to find AprilTags, extracts pose estimations, and displays the feed locally.
*   **`signaling_server.py`**
    Local HTTP signaling server for SDP offer/answer exchange to orchestrate the WebRTC connection.
*   **`constants/config.py`**
    Shared configuration file containing IP addresses, ports, and camera settings.
*   **`libs/`**
    Helper functions and processing logic (e.g., WebRTC signaling clients, image processing, drawing modules).
*   **`camera_calibration/`**
    Calibration utilities and outputs (`camera_matrix.npy` and `dist_coeffs.npy` which are required for pose estimation).
*   **`requirements.txt`**
    Python dependencies required for the project.

## Requirements
*   Python 3.10+ (recommended)
*   A connected webcam
*   An printed AprilTag from the **tag25h9** family

## Installation (Windows PowerShell)

From the `python` folder, run the following commands to set up the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running the WebRTC Demo

To run the full stack, you need to open three separate PowerShell windows in this directory, ensuring the virtual environment is activated in each.

1.  **Start the Signaling Server:**
    ```powershell
    python .\signaling_server.py
    ```

2.  **Start the Receiver / Processor:**
    ```powershell
    python .\video_processor.py
    ```

3.  **Start the Camera Offerer (Raspberry):**
    ```powershell
    python .\raspberry.py
    ```

## Controls
*   Press `Esc` in the webcam sender console to stop the capture stream.
*   Press `Esc` in the OpenCV video window to close the receiver.

## Output Details
Console output example from the processing video window:
`id:3,x:12.4,y:-1.8,z:45.9,pitch:7.2`

*   Coordinates are printed in centimeters (pose translation multiplied by 100).
*   The literal tag scale (e.g. `tag_size` = 0.05 meters) depends on your configuration or printing size.

## Troubleshooting

1.  **No camera image / Camera access error**
    *   Ensure no other apps (like Zoom or OBS) are using the webcam.
    *   Modify the camera name or index settings inside `constants/config.py` (e.g. changing `CAMERA_NAME` or `CAMERA_RESOLUTION`).
2.  **Bad pose/distance estimates**
    *   Recheck `camera_matrix.npy` and `dist_coeffs.npy` from your specific camera calibration process.
    *   Confirm your physical tag size matches the scaling parameter expected by the detection module.
3.  **No tags detected**
    *   Ensure the printed tag belongs to the `tag25h9` family.
    *   Ensure you have bright lighting and wait for the camera focus to adapt.
