import numpy as np
from scipy.spatial.transform import Rotation as R
import cv2

__all__ = ["process_image", "draw_pose"]

def process_image(frame, tag):
    center = tag.center.astype(np.int32)
    t = tag.pose_t.flatten()

    distancia = np.linalg.norm(t)*100 - 20
    
    rot = R.from_matrix(np.eye(3))
    
    try:
        rot = R.from_matrix(tag.pose_R)
    except:
        pass
        
    yaw, pitch, roll = rot.as_euler('zyx', degrees=True)

    corners = tag.corners.astype(np.int32)

    cv2.circle(frame, (center[0], center[1]), 3, (0, 255, 0), -1)
    cv2.putText(frame, f"{distancia.round(1)}cm", (corners[1][0], corners[1][1]+60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    #cv2.putText(frame, f"{yaw.round(2)}", (center[0], center[1]+150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"{pitch.round(1)}deg", (corners[1][0]+100, corners[1][1]+60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    #cv2.putText(frame, f"{roll.round(2)}", (center[0], center[1]+200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    cv2.putText(frame, f"tag {tag.tag_id}", (corners[1][0], corners[1][1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.polylines(frame, [corners], True, (0, 255, 0), thickness = 2)

    return pitch

def draw_pose(overlay, camera_params, tag_size, pose, z_sign=1):

    opoints = np.array([
        2, 0, 0,
         0, 0, 0,
         0,  2, 0,
         0, 0, -2,
    ]).reshape(-1, 1, 3) * 0.5 * tag_size

    fx, fy, cx, cy = camera_params

    K = np.array([
        fx, 0, cx,
        0, fy, cy,
        0, 0, 1
    ]).reshape(3, 3)

    rvec, _ = cv2.Rodrigues(pose[:3, :3])
    tvec = pose[:3, 3]

    dcoeffs = np.zeros(5)

    ipoints, _ = cv2.projectPoints(
        opoints,
        rvec,
        tvec,
        K,
        dcoeffs
    )

    ipoints = np.round(ipoints).astype(int)
    ipoints = [tuple(pt) for pt in ipoints.reshape(-1, 2)]

    # X axis - Red
    cv2.line(overlay, ipoints[0], ipoints[1], (0, 0, 255), 2)

    # Y axis - Green
    cv2.line(overlay, ipoints[1], ipoints[2], (0, 255, 0), 2)

    # Z axis - Blue
    cv2.line(overlay, ipoints[1], ipoints[3], (255, 0, 0), 2)

    font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(
        overlay,
        'X',
        ipoints[0],
        font,
        0.5,
        (0, 0, 255),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        overlay,
        'Y',
        ipoints[2],
        font,
        0.5,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        overlay,
        '-Z',
        ipoints[3],
        font,
        0.5,
        (255, 0, 0),
        2,
        cv2.LINE_AA
    )
