"""Communication module for Fork Lift application.

This module handles all external communications:
- MQTT broker connection for receiving control commands
- Serial port communication with hardware (microcontroller)
- WebSocket communication for streaming video or telemetry
- Command parsing and routing

All communication components are optional and the application will degrade
gracefully if any communication method is unavailable.
"""
import certifi
import json
import queue
import threading
import logging
from .config import config
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

def create_and_start_mqtt(username, password, host, port, on_connect=None, on_message=None):
    """Create, configure and (optionally) connect an MQTT client.

    Attempts to create and configure an MQTT client using the paho-mqtt library.
    If paho-mqtt is not installed, returns a mock client that accepts all calls
    but does nothing, allowing the application to continue running.

    Args:
        username (str | None): Username for MQTT authentication
        password (str | None): Password for MQTT authentication
        host (str | None): MQTT broker hostname or IP address
        port (int | None): MQTT broker port number
        on_connect (callable | None): Callback function for connection events
        on_message (callable | None): Callback function for received messages

    Returns:
        paho.mqtt.client.Client | _MockMQTTClient: MQTT client instance.
            A real client if paho-mqtt is available, a mock client otherwise.
            Connection is only attempted if both host and port are provided.
    """
    try:
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
            except Exception as e:
                logger.debug(f"MQTT connection failed: {e}")
                pass

        return client
    except ImportError:
        logger.debug("paho-mqtt not available, creating mock MQTT client")
        return _MockMQTTClient()


class _MockMQTTClient:
    """Mock MQTT client for when paho-mqtt is not available."""
    
    def __init__(self):
        self.user_data = None
    
    def tls_set(self, *args, **kwargs):
        pass
    
    def username_pw_set(self, *args, **kwargs):
        pass
    
    def on_connect(self, *args, **kwargs):
        pass
    
    def on_message(self, *args, **kwargs):
        pass
    
    def connect(self, *args, **kwargs):
        pass
    
    def user_data_set(self, data):
        self.user_data = data
    
    def loop_start(self):
        pass
    
    def loop_stop(self):
        pass
    
    def disconnect(self):
        pass
    
    def loop_read(self):
        pass
    
    def loop_write(self):
        pass
    
    def loop_misc(self):
        pass

def step_mqtt(client):
    """Run a single mqtt client network step (non-blocking)."""
    try:
        client.loop_read()
        client.loop_write()
        client.loop_misc()
    except Exception:
        # ignore network errors here; callers may log
        pass


def start_serial_reader(serial_port, response_queue: "queue.Queue[str]", stop_event: threading.Event):
    """Start a dedicated thread that performs blocking serial reads and puts lines into a queue."""
    def _worker():
        while not stop_event.is_set():
            if serial_port is None:
                logger.debug("Serial port not available, skipping read")
                response_queue.task_done()
                continue

            try:
                line = serial_port.readline().decode().strip()
                if line:
                    response_queue.put(line)
            except Exception as e:
                logger.debug(f"Serial reader error: {e}")
            finally:
                response_queue.task_done()

    thread = threading.Thread(target=_worker, name="serial-reader", daemon=True)
    thread.start()
    return thread
 
def start_serial_writer(serial_port, command_queue: "queue.Queue[str]", stop_event: threading.Event):
    """Start a dedicated thread that performs blocking serial writes from a queue."""
    def _worker():
        while not stop_event.is_set():
            try:
                cmd = command_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if serial_port is None:
                logger.debug(f"Serial port not available, discarding command: {cmd}")
                command_queue.task_done()
                continue

            try:
                serial_port.write(cmd.encode())
            except Exception as e:
                logger.debug(f"Serial writer error: {e}")
            finally:
                command_queue.task_done()

    thread = threading.Thread(target=_worker, name="serial-writer", daemon=True)
    thread.start()
    return thread

async def send_websocket(url, message):
    """Send a message to a websocket server (no-op if url falsy)."""
    if not url:
        return
    try:
        import websockets
        try:
            async with websockets.connect(url) as websocket:
                await websocket.send(message)
        except Exception as e:
            logger.debug(f"WebSocket send error: {e}")
    except ImportError:
        logger.debug("websockets not available for sending")

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

    The callback expects payloads like {"modo": 0, "direcao": "up", "velocidade": "100"}.
    If `serial_port` is falsy, the function will only log the parsed command.
    """
    def _to_serial_command(modo: Optional[str], direction: Optional[str], velocidade: int) -> Optional[str]:
        if modo == 0:
            config.is_autonomous = False
            if direction == "up":
                return f"0 {velocidade},{velocidade}"
            if direction == "down":
                return f"0 {-velocidade},{-velocidade}"
            if direction == "left":
                return f"0 {-velocidade},{velocidade}"
            if direction == "right":
                return f"0 {velocidade},{-velocidade}"
            return None
        if modo == 1:
            config.is_autonomous = True
            return "1"
        if modo == 3:
            config.is_autonomous = False
            if direction == "up":
                return f"3 {velocidade}"
            if direction == "down":
                return f"3 {-velocidade}"
            return None

    def _on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode()
            logger.info(f"Topic: {msg.topic} | Payload: {payload}")
            json_string = json.loads(payload)
            modo = json_string.get("modo")
            direction = json_string.get("direcao")
            velocidade = int(json_string.get("velocidade", 0))

            command_queue = userdata.get("command_queue") if isinstance(userdata, dict) else None
            command = _to_serial_command(modo, direction, velocidade)

            if command_queue and command:
                command_queue.put(command)
            elif serial_port and command:
                try:
                    serial_port.write(command.encode())
                except Exception as e:
                    logger.debug(f"Serial write error: {e}")
            else:
                logger.debug(f"Command not sent (no destination): {command}")
        except Exception as e:
            logger.debug(f"MQTT message handling error: {e}")

    return _on_message
