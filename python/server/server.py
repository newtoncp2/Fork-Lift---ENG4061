from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
import json 
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

#mqtt
BROKER = "mqtt.janks.dev.br"     
PORT   = 8883
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

client = mqtt.Client(client_id="raspipi")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

def on_connect(client, userdata, flags, rc):
    print("Conectado com código:", rc)
    client.subscribe("empilhadeira/controle")  # assina o tópico ao conectar

def on_message(client, userdata, msg):
    print("Chegou mensagem no tópico:", msg.topic)
    payload = msg.payload.decode("utf-8")
    print("Payload bruto:", payload)
    
client.tls_set()  
client.on_connect = on_connect
client.on_message = on_message

app = Flask(__name__)

@app.route("/", methods = ["GET", "POST"])
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
        retorno = client.publish("empilhadeira/controle", json.dumps(dados), qos=0, retain=False)
        print("Publicou com retorno:", retorno)

        return {"status": "ok"}


    else:
        return render_template("menu.html")

def main():
    try:
        client.loop_start()
        app.run(port=5002, debug=False)
    except KeyboardInterrupt:
        print("Encerrando aplicação...")
    except Exception as e:
        print("Erro:", e)
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()