import os
import time
import logging
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def setup_resources(base_dir: str | None = None):
    """Initialize and return runtime resources as a dict.

    Resources returned:
      - ser: serial.Serial or None
      - mqtt_username, mqtt_password, mqtt_host, mqtt_port, web_socket_url
      - camera_matrix, dist_coeffs, camera_params
      - tag_size, at_detector, cap
    
    All resources are optional and will be None if unavailable.
    """
    # Try serial connection (non-fatal)
    ser = None
    try:
        import serial
        ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
        logger.info("Serial connection established")
    except Exception as e:
        logger.debug(f"Serial connection not available: {e}")
        ser = None

    # small delay to let serial initialize if present
    if ser:
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

    # Load camera calibration (non-fatal)
    camera_matrix = None
    dist_coeffs = None
    camera_params = None
    
    try:
        camera_matrix = np.load(str(base / "camera_calibration" / "camera_matrix.npy"))
        dist_coeffs = np.load(str(base / "camera_calibration" / "dist_coeffs.npy"))
        camera_params = (
            camera_matrix[0, 0],
            camera_matrix[1, 1],
            camera_matrix[0, 2],
            camera_matrix[1, 2],
        )
        logger.info("Camera calibration loaded")
    except Exception as e:
        logger.debug(f"Camera calibration files not available: {e}")
        # Set default dummy calibration values
        camera_matrix = np.eye(3)
        dist_coeffs = np.zeros(5)
        camera_params = (800.0, 800.0, 320.0, 240.0)  # Default focal length and principal point

    tag_size = 0.05

    # Load AprilTag detector (non-fatal)
    at_detector = None
    try:
        from pupil_apriltags import Detector
        at_detector = Detector(
            families="tag25h9",
            nthreads=1,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0,
        )
        logger.info("AprilTag detector initialized")
    except Exception as e:
        logger.debug(f"AprilTag detector not available: {e}")
        at_detector = None

    # Try camera connection (non-fatal)
    cap = None
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.debug("Camera not available")
            cap = None
        else:
            logger.info("Camera initialized")
    except Exception as e:
        logger.debug(f"Camera not available: {e}")
        cap = None

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
