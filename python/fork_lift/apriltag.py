import cv2
import numpy as np
from .drawing import draw_pose, process_image
import asyncio
from .setup import setup_resources
from .connections import (
    create_and_start_mqtt,
    step_mqtt as step_mqtt_client,
    send_websocket as send_ws,
    safe_disconnect,
    make_on_connect,
    make_on_message,
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

# MQTT callbacks are created in `fork_lift.connections` using factories

print("starting mqtt...")
# create and start the mqtt client (connection attempt is non-fatal)
mqtt_client = create_and_start_mqtt(
    mqtt_username,
    mqtt_password,
    mqtt_host,
    mqtt_port,
    on_connect=make_on_connect(["empilhadeira/controle"]),
    on_message=make_on_message(ser),
)

async def main():
    while cap.isOpened():
        step_mqtt_client(mqtt_client)
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
                x_coord = coords[0][0]
                y_coord = coords[1][0]
                z_coord = coords[2][0]

                t = tag.pose_t.flatten()
                distancia = np.linalg.norm(t)*100

                # TODO: Inserir tomada de decisão
                coord_str = f"id:{tag_id},x:{coords[0][0]},y:{coords[1][0]},z:{coords[2][0]},pitch:{pitch},distancia:{distancia}"
                print(coord_str)
                # ser.write(coord_str)

        # Send image via websocket
        ret, encoded_frame = cv2.imencode('.jpg', undistorted)

        if ret:
            await send_ws(web_socket_url, encoded_frame.tobytes())

def _run_main():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        cap.release()
        if ser is not None:
            ser.close()
        try:
            safe_disconnect(mqtt_client)
        except Exception:
            pass

if __name__ == '__main__':
    _run_main()
