import os
import logging
import numpy as np
import asyncio
import queue
import threading
import time
from .setup import setup_resources
from .connections import (
    create_and_start_mqtt,
    send_websocket as send_ws,
    safe_disconnect,
    make_on_connect,
    make_on_message,
    start_serial_writer,
)

# Centralized resource setup
_RES = setup_resources()

# expose setup values as module-level names (existing code expects these)
ser = _RES['ser']
mqtt_username = _RES['mqtt_username']
mqtt_password = _RES['mqtt_password']
mqtt_host = _RES['mqtt_host']
mqtt_port = _RES['mqtt_port']
web_socket_url = _RES['web_socket_url']

camera_matrix = _RES['camera_matrix']
dist_coeffs = _RES['dist_coeffs']
camera_params = _RES['camera_params']
tag_size = _RES['tag_size']
at_detector = _RES['at_detector']
cap = _RES['cap']

# runtime `debug` variable controls debug logging; can be overridden by
# setting the environment variable `DEBUG=1` (or 'true', 'yes'). Users can also
# set `fork_lift.apriltag.debug = True` before calling functions in this module
# to enable debug logging programmatically.
debug = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")

# Configure logging according to `debug` variable. Consumers of this package
# may reconfigure the logging handlers if they prefer different formatting.
_level = logging.DEBUG if debug else logging.INFO
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s", level=_level
)
logger = logging.getLogger(__name__)

# MQTT callbacks are created in `fork_lift.connections` using factories

frame_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=1)
ws_queue: "queue.Queue[bytes]" = queue.Queue(maxsize=1)
command_queue: "queue.Queue[str]" = queue.Queue(maxsize=100)
stop_event = threading.Event()

last_tag = 0
SEARCH_MODE_TIMEOUT = 6.0  # seconds without tag detection before sending search mode command

logger.info("starting mqtt...")
# create and start the mqtt client (connection attempt is non-fatal)
mqtt_client = create_and_start_mqtt(
    mqtt_username,
    mqtt_password,
    mqtt_host,
    mqtt_port,
    on_connect=make_on_connect(["empilhadeira/controle"]),
    on_message=make_on_message(ser),
)
mqtt_client.user_data_set({"command_queue": command_queue})


def _put_latest(work_queue: queue.Queue, value):
    if work_queue.full():
        try:
            work_queue.get_nowait()
        except queue.Empty:
            pass
    try:
        work_queue.put_nowait(value)
    except queue.Full:
        pass


def _capture_worker():
    """Capture frames from camera if available."""
    if cap is None:
        logger.info("Camera not available, skipping capture")
        return
        
    while not stop_event.is_set() and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        _put_latest(frame_queue, frame)


def _vision_worker():
    """Process frames for tags if detector is available."""
    global last_tag
    
    if at_detector is None:
        logger.info("AprilTag detector not available, skipping vision processing")
        return
    
    try:
        import cv2
        from .drawing import draw_pose, process_image
    except ImportError as e:
        logger.warning(f"Vision dependencies not available: {e}")
        return
    
    while not stop_event.is_set():        
        # Get the latest frame from the queue, if available
        try:
            frame = frame_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        try:
            undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
            gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)

            tags = at_detector.detect(
                gray,
                estimate_tag_pose=True,
                camera_params=camera_params,
                tag_size=tag_size,
            )

            if tags:
                last_tag = time.time()
                for tag in tags:
                    pitch = process_image(undistorted, tag)

                    pose = np.eye(4)
                    pose[:3, :3] = tag.pose_R
                    pose[:3, 3] = tag.pose_t.flatten()

                    draw_pose(undistorted, camera_params, tag_size, pose)

                    coords = np.array([tag.pose_t[0], tag.pose_t[1], tag.pose_t[2]]) * 100
                    t = tag.pose_t.flatten()
                    distancia = np.linalg.norm(t) * 100

                    # TODO: fazer lógica de controle
                    coord_str = (
                        f"id:{tag.tag_id},x:{coords[0][0]},y:{coords[1][0]},"
                        f"z:{coords[2][0]},pitch:{pitch},distancia:{distancia}"
                    )
                    logger.debug(coord_str)
                    
            if time.time() - last_tag > SEARCH_MODE_TIMEOUT:
                last_tag = time.time()
                logger.debug(f"No tags detected for {SEARCH_MODE_TIMEOUT} seconds, sending search mode command")
                command_queue.put("2")

            ret, encoded_frame = cv2.imencode('.jpg', undistorted)
            if ret:
                _put_latest(ws_queue, encoded_frame.tobytes())
        except Exception as e:
            logger.debug(f"Vision processing error: {e}")


async def _websocket_sender():
    while not stop_event.is_set():
        try:
            payload = ws_queue.get_nowait()
        except queue.Empty:
            await asyncio.sleep(0.01)
            continue
        await send_ws(web_socket_url, payload)

async def main():
    serial_thread = start_serial_writer(ser, command_queue, stop_event)
    capture_thread = threading.Thread(target=_capture_worker, name="capture-worker", daemon=True)
    vision_thread = threading.Thread(target=_vision_worker, name="vision-worker", daemon=True)

    capture_thread.start()
    vision_thread.start()

    try:
        mqtt_client.loop_start()
    except Exception:
        pass

    try:
        await _websocket_sender()
    finally:
        stop_event.set()
        capture_thread.join(timeout=1.0)
        vision_thread.join(timeout=1.0)
        serial_thread.join(timeout=1.0)

def _run_main():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        stop_event.set()
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass
        try:
            mqtt_client.loop_stop()
        except Exception:
            pass
        try:
            safe_disconnect(mqtt_client)
        except Exception:
            pass

if __name__ == '__main__':
    _run_main()
