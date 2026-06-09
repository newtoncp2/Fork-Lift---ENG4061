"""
config.py
Centralized configuration values and environment variables.
"""

# Signaling server settings
SIGNALING_SERVER_IP = "127.0.0.1"
SIGNALING_SERVER_PORT = 8765
SIGNALING_BASE_URL = f"http://{SIGNALING_SERVER_IP}:{SIGNALING_SERVER_PORT}"

# Camera settings
CAMERA_NAME = "Logi C270 HD WebCam"
CAMERA_RESOLUTION = "640x480"
MEDIA_PLAYER_FORMAT = "dshow"  # Use "v4l2" for Linux and "dshow" for Windows