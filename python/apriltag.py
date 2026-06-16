import cv2
import numpy as np
from pupil_apriltags import Detector
from drawing import draw_pose, process_image
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
import certifi
import serial
import time
import asyncio
import websockets

# For Arduino Uno/Mega, it is usually '/dev/ttyACM0'. For Nano, it is often '/dev/ttyUSB0'
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
except:
    print("Erro ao conectar serial")

time.sleep(2) # Wait for connection to initialize

# Load the variables
load_dotenv()

mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")
mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = int(os.getenv("MQTT_PORT"))
web_socket_url = os.getenv("WEB_SOCKET_URL")

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
   nthreads=2,
   quad_decimate=1.0,
   quad_sigma=0.0,
   refine_edges=1,
   decode_sharpening=0.25,
   debug=0
)

cap = cv2.VideoCapture(0)

# Callback for when the client receives a CONNACK response from the broker
def on_connect(client, userdata, flags, reason_code):
    print(f"Connected with code: {reason_code}")
    client.subscribe("empilhadeira/controle")

# Callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic} | Payload: {msg.payload.decode()}")

    # Envia comandos do mqtt para o arduino
    try:
        ser.write(msg.payload)
    except:
        print("Erro ao conectar serial")

def start_mqtt():
    global mqtt_client
    print("starting mqtt...")
    mqtt_client = mqtt.Client()
    mqtt_client.tls_set(certifi.where())
    mqtt_client.username_pw_set(username=mqtt_username, password=mqtt_password)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(mqtt_host, mqtt_port, 60)

def step_mqtt():
    global mqtt_client
    mqtt_client.loop_read()
    mqtt_client.loop_write()
    mqtt_client.loop_misc()

async def send_websocket(message):
    async with websockets.connect(web_socket_url) as websocket:
        await websocket.send(message)

start_mqtt()

async def main():
    try:
        while cap.isOpened():
            step_mqtt()
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
                await send_websocket(encoded_frame.tobytes())

    except KeyboardInterrupt:
        cap.release()
        if ser != None:
            ser.close()

# Start the event loop and run the main() coroutine
asyncio.run(main())