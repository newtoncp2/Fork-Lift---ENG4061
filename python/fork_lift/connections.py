import certifi
import json
from typing import Iterable, Optional

def create_and_start_mqtt(username, password, host, port, on_connect=None, on_message=None):
    """Create, configure and (optionally) connect an MQTT client.

    Returns the paho.mqtt.client.Client instance. Connection is attempted
    only if `host` and `port` are provided.
    """
    import paho.mqtt.client as mqtt

    client = mqtt.Client()
    client.tls_set(certifi.where())
    if username and password:
        client.username_pw_set(username=username, password=password)
    if on_connect:
        client.on_connect = on_connect
    if on_message:
        client.on_message = on_message

    if host and port:
        try:
            client.connect(host, port, 60)
        except Exception:
            # Do not raise; caller can handle missing broker at runtime
            pass

    return client

def step_mqtt(client):
    """Run a single mqtt client network step (non-blocking)."""
    try:
        client.loop_read()
        client.loop_write()
        client.loop_misc()
    except Exception:
        # ignore network errors here; callers may log
        pass

async def send_websocket(url, message):
    """Send a message to a websocket server (no-op if url falsy)."""
    if not url:
        return
    import websockets
    try:
        async with websockets.connect(url) as websocket:
            await websocket.send(message)
    except Exception:
        # ignore errors; caller may log
        pass

def safe_disconnect(client):
    try:
        client.disconnect()
    except Exception:
        pass


def make_on_connect(subscribe_topics: Optional[Iterable[str]] = None):
    """Return an `on_connect` callback that subscribes to the given topics."""
    topics = list(subscribe_topics) if subscribe_topics else []

    def _on_connect(client, userdata, flags, reason_code):
        print(f"Connected with code: {reason_code}")
        for t in topics:
            try:
                client.subscribe(t)
            except Exception:
                pass

    return _on_connect


def make_on_message(serial_port: Optional[object] = None):
    """Return an `on_message` callback that parses JSON payloads and writes to serial.

    The callback expects payloads like {"direcao": "up", "velocidade": "100"}.
    If `serial_port` is falsy, the function will only log the parsed command.
    """
    def _on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode()
            print(f"Topic: {msg.topic} | Payload: {payload}")
            json_string = json.loads(payload)
            direction = json_string.get("direcao")
            velocidade = int(json_string.get("velocidade", 0))

            if serial_port:
                if direction == "up":
                    serial_port.write(f"{velocidade},{velocidade}".encode())
                elif direction == "down":
                    serial_port.write(f"{-velocidade},{-velocidade}".encode())
                elif direction == "left":
                    serial_port.write(f"{-velocidade},{velocidade}".encode())
                elif direction == "right":
                    serial_port.write(f"{velocidade},{-velocidade}".encode())
        except Exception as e:
            print("MQTT message handling error:", e)

    return _on_message
