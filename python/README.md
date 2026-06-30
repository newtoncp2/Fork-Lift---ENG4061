Fork-Lift AprilTag Detection (Python)
=================================

Overview
--------
This project detects AprilTags from a webcam feed, estimates each tag pose, and overlays:
- Tag outline and ID
- Distance (cm)
- Pitch angle (degrees)
- 3D pose axes (X, Y, -Z)

For every detected tag, the script also prints one line to the console:
id, x, y, z, pitch

Project Files
-------------
- apriltag.py
  Main application loop. Loads camera calibration, captures webcam frames, detects tags, draws overlays, and prints pose values.

- drawing.py
  Helper functions:
  - process_image(frame, tag): draws text/contours and returns pitch
  - draw_pose(overlay, camera_params, tag_size, pose): draws 3D axes

- requirements.txt
  Python dependencies.

- camera_calibration/
  Folder containing camera calibration utilities and outputs. It includes scripts used to capture calibration images and compute intrinsics, and stores the generated `camera_matrix.npy` and `dist_coeffs.npy`.

    - camera_matrix.npy
        Camera intrinsic matrix used for undistortion and pose estimation.

    - dist_coeffs.npy
        Camera distortion coefficients used for undistortion.

Requirements
------------
- Python 3.10+ (recommended)
- A connected webcam
- An AprilTag from family tag25h9

Install (Windows PowerShell)
-----------------------------
From this folder (`python`), run:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Run
---
    python .\apriltag.py

Controls
--------
- Press `q` in the video window to quit.

Output
------
Console output example:
    id:3,x:12.4,y:-1.8,z:45.9,pitch:7.2

Notes
-----
- Coordinates are printed in centimeters (pose translation multiplied by 100).
- `tag_size` is currently set to 0.05 (meters) in `apriltag.py`.
  Update it if your physical tag has a different size.
- Detection is configured for family `tag25h9`.
- If your camera is not index 0, change `cv2.VideoCapture(0)` in `apriltag.py`.

Troubleshooting
---------------
1) No camera image
   - Close apps using the webcam.
   - Try another index in `cv2.VideoCapture(...)`.

2) Bad pose/distance estimates
   - Recheck `camera_matrix.npy` and `dist_coeffs.npy`.
   - Confirm `tag_size` matches your real tag size in meters.

3) No tags detected
   - Ensure the printed tag belongs to family `tag25h9`.
   - Improve lighting and keep the tag in focus.
