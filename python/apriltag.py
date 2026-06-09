import cv2
import numpy as np
from pupil_apriltags import Detector
from drawing import draw_pose, process_image

camera_matrix = np.load("camera_calibration/camera_matrix.npy")
dist_coeffs = np.load("camera_calibration/dist_coeffs.npy")

# fx, fy, cx, cy
camera_params = (
    camera_matrix[0, 0],
    camera_matrix[1, 1],
    camera_matrix[0, 2],
    camera_matrix[1, 2]
)

tag_size = 0.05

at_detector = Detector(
   families="tag25h9",
   nthreads=1,
   quad_decimate=1.0,
   quad_sigma=0.0,
   refine_edges=1,
   decode_sharpening=0.25,
   debug=0
)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Remove camera distortion
    undistorted = cv2.undistort(
        frame,
        camera_matrix,
        dist_coeffs
    )

    # Turn grayscale
    gray = cv2.cvtColor(
        undistorted,
        cv2.COLOR_BGR2GRAY
    )

    # Detect AprilTags
    tags = at_detector.detect(gray,
        estimate_tag_pose=True,
        camera_params=camera_params,
        tag_size=tag_size) 
    
    if tags:
        for idx, tag in enumerate(tags):
            # Outline tag and write information
            pitch = process_image(undistorted, tag)

            # Build 4x4 pose matrix
            pose = np.eye(4)
            pose[:3, :3] = tag.pose_R
            pose[:3, 3] = tag.pose_t.flatten()

            # Draw XYZ axis
            draw_pose(
                undistorted,
                camera_params,
                tag_size,
                pose
            )

            coords = np.array([tag.pose_t[0], tag.pose_t[1], tag.pose_t[2]])*100
            tag_id = tag.tag_id

            print(f"id:{tag_id},x:{coords[0][0]},y:{coords[1][0]},z:{coords[2][0]},pitch:{pitch}")


cap.release()