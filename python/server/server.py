from flask import Flask, request, render_template
import threading
from flask_sock import Sock
import os
import json
import paho.mqtt.client as mqtt
import cv2
from pathlib import Path
import numpy as np
from .drawing import draw_pose, process_image
from pupil_apriltags import Detector
from dotenv import load_dotenv

load_dotenv()

# mqtt
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

base = Path(__file__).resolve().parent.parent

camera_matrix = np.load(str(base / "camera_calibration" / "camera_matrix.npy"))
dist_coeffs = np.load(str(base / "camera_calibration" / "dist_coeffs.npy"))
camera_params = (
    camera_matrix[0, 0],
    camera_matrix[1, 1],
    camera_matrix[0, 2],
    camera_matrix[1, 2],
)

def on_connect(client, userdata, flags, rc):
    print("Conectado com código:", rc)
    client.subscribe("empilhadeira/controle")  # assina o tópico ao conectar


def on_message(client, userdata, msg):
    print("Chegou mensagem no tópico:", msg.topic)
    payload = msg.payload.decode("utf-8")
    print("Payload bruto:", payload)

client = mqtt.Client(client_id="python-publisher2")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.tls_set()

app = Flask(__name__)
sock = Sock(app)  # Inicializa o suporte a WebSockets nativos

# Conjunto para armazenar todos os clientes conectados (a página web)
connected_clients = set()
clients_lock = threading.Lock()


@app.route("/", methods=["GET", "POST"])
def menu():
    if request.method == "POST":
        print("Recebi alguma coisa")

        dados = request.get_json()
        print(dados)

        direcao = dados["direcao"]
        velocidade = dados["velocidade"]
        modo = dados["modo"]

        print("Direção: ", direcao)
        print("Velocidade: ", velocidade)
        print("modo: ", modo)
        retorno = client.publish(
            "empilhadeira/controle", json.dumps(dados), qos=0, retain=False
        )
        print("Publicou com retorno:", retorno)

        return {"status": "ok"}

    else:
        return render_template("menu.html")


# Rota para WebSockets puros
@sock.route("/video_feed")
def video_feed(ws):
    # Adiciona este cliente à lista de transmissores
    with clients_lock:
        connected_clients.add(ws)
        
    try:
        at_detector = Detector(
            families="tag25h9",
            nthreads=1,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0,
        )
        while True:
            # Recebe a imagem do robô
            image_data = ws.receive()
            
            if image_data is None:
                break
            
            if not isinstance(image_data, (bytes, bytearray)):
                continue

            if len(image_data) <= 10:
                continue
            
            frame = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            tag_size = 0.05
            
            tags = at_detector.detect(
                gray,
                estimate_tag_pose=True,
                camera_params=camera_params,
                tag_size=tag_size,
            )
            
            for tag in tags:
                process_image(frame, tag)  # Processa a imagem (desenho de pose, etc.)
                
                pose = np.eye(4)
                pose[:3, :3] = tag.pose_R
                pose[:3, 3] = tag.pose_t.flatten()

                draw_pose(frame, camera_params, tag_size, pose)
                
            image_data = cv2.imencode(".jpg", frame)[1].tobytes()

            # Retransmite para todos os outros clientes conectados (a página web)
            with clients_lock:
                recipients = [
                    client_ws
                    for client_ws in connected_clients
                    if client_ws is not ws
                ]
                
            disconnected = []

            for client_ws in recipients:
                try:
                    client_ws.send(image_data)
                except Exception:
                    disconnected.append(client_ws)
                    
            if disconnected:
                with clients_lock:
                    for client_ws in disconnected:
                        connected_clients.discard(client_ws)
                        
    except Exception as e:
        if "1000" not in str(e):
            print(f"Erro no WebSocket: {e}")
    finally:
        with clients_lock:
            connected_clients.discard(ws)


def main():
    try:
        client.loop_start()
        app.run(
            host="0.0.0.0",
            port=5002,
            debug=False,
            threaded=True,
            use_reloader=False,
        )
    except KeyboardInterrupt:
        print("Encerrando aplicação...")
    except Exception as e:
        print("Erro:", e)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
