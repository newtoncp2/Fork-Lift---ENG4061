import os
import time
from pathlib import Path
import serial
import numpy as np
from pupil_apriltags import Detector
import cv2
from dotenv import load_dotenv


def setup_resources(base_dir: str | None = None):
    """Initialize and return runtime resources as a dict.

    Resources returned:
      - ser: serial.Serial or None
      - mqtt_username, mqtt_password, mqtt_host, mqtt_port, web_socket_url
      - camera_matrix, dist_coeffs, camera_params
      - tag_size, at_detector, cap
    """
    # Try serial connection (non-fatal)
    ser = None
    try:
        ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
    except Exception:
        # leave ser as None if not available
        ser = None

    # small delay to let serial initialize if present
    time.sleep(2)

    # Load environment vars from .env if present
    load_dotenv()

    mqtt_username = os.getenv("MQTT_USERNAME")
    mqtt_password = os.getenv("MQTT_PASSWORD")
    mqtt_host = os.getenv("MQTT_HOST")
    mqtt_port = int(os.getenv("MQTT_PORT")) if os.getenv("MQTT_PORT") else None
    web_socket_url = os.getenv("WEB_SOCKET_URL")

    # Resolve base dir
    if base_dir:
        base = Path(base_dir)
    else:
        base = Path(__file__).resolve().parent.parent

    # Load camera calibration
    camera_matrix = np.load(str(base / "camera_calibration" / "camera_matrix.npy"))
    dist_coeffs = np.load(str(base / "camera_calibration" / "dist_coeffs.npy"))

    camera_params = (
        camera_matrix[0, 0],
        camera_matrix[1, 1],
        camera_matrix[0, 2],
        camera_matrix[1, 2],
    )

    tag_size = 0.05

    at_detector = Detector(
        families="tag25h9",
        nthreads=1,
        quad_decimate=1.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0,
    )

    cap = cv2.VideoCapture(0)

    return {
        "ser": ser,
        "mqtt_username": mqtt_username,
        "mqtt_password": mqtt_password,
        "mqtt_host": mqtt_host,
        "mqtt_port": mqtt_port,
        "web_socket_url": web_socket_url,
        "camera_matrix": camera_matrix,
        "dist_coeffs": dist_coeffs,
        "camera_params": camera_params,
        "tag_size": tag_size,
        "at_detector": at_detector,
        "cap": cap,
    }
