from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sock import Sock
import os
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

# mqtt
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

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

app = Flask(__name__)
sock = Sock(app)  # Inicializa o suporte a WebSockets nativos

# Conjunto para armazenar todos os clientes conectados (a página web)
connected_clients = set()


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
    connected_clients.add(ws)
    try:
        while True:
            # Recebe a imagem do robô
            image_data = ws.receive()

            # Retransmite para todos os outros clientes conectados (a página web)
            if image_data and len(image_data) > 10:
                for client in connected_clients.copy():
                    if client != ws:
                        try:
                            client.send(image_data)
                        except Exception:
                            connected_clients.remove(client)
    except Exception as e:
        if "1000" not in str(e):
            print(f"Erro no WebSocket: {e}")
    finally:
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
