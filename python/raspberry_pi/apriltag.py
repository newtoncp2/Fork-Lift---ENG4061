import os
import logging
import numpy as np
import asyncio
import queue
import threading
import time
import json
from .config import config
from .setup import setup_resources
from .connections import (
    create_and_start_mqtt,
    safe_disconnect,
    make_on_connect,
    make_on_message,
    start_serial_writer,
    start_serial_reader
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
response_queue: "queue.Queue[str]" = queue.Queue(maxsize=100)
frame_queue_mutex = threading.Lock()
ws_queue_mutex = threading.Lock()
command_queue_mutex = threading.Lock()
response_queue_mutex = threading.Lock()

stop_event = threading.Event()

# Global variables
busca = [f"1 {np.pi/3}\n", f"1 -{np.pi/3}\n", f"1 -{np.pi/3}\n",f"1 {np.pi/3}\n", "2 0.35\n"]
aprox = ["","",""]
ideal = ["3 95",f"2 0.15",f"3 5",f"2 -0.2", f"3 -95"] # AJUSTAR VALORES
etapa_busca = 0
etapa_aprox = 0
etapa_ideal = 0
estado_anterior = "buscar"
x0, z0, z_lin, kx, kz = 0.0, 0.0, 0.0, 0.0, 0.0
cont = 0
#SEARCH_MODE_TIMEOUT = 5.0  # seconds without tag detection before sending search mode command
TARGET_TAG_ID = os.getenv("TARGET_TAG_ID", [0, 1])
tag_counter = 0
try:
    TARGET_TAG_ID = json.loads(TARGET_TAG_ID)
except (ValueError, TypeError):
    logger.warning(f"Invalid TARGET_TAG_ID: {TARGET_TAG_ID}")
    TARGET_TAG_ID = [0, 1]

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
mqtt_client.user_data_set({"command_queue": command_queue, "command_queue_mutex": command_queue_mutex})

def _put_latest(work_queue: queue.Queue, work_queue_mutex: threading.Lock, value):
    with work_queue_mutex:
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
        _put_latest(frame_queue, frame_queue_mutex, frame)
        
        try:
            import cv2
        except ImportError as e:
            logger.warning(f"Vision dependencies not available: {e}")
            return
        
        ret, encoded_frame = cv2.imencode('.jpg', frame)
        if ret:
            _put_latest(ws_queue, ws_queue_mutex, encoded_frame.tobytes())   


def _vision_worker():
    """Process frames for tags if detector is available."""
    #global last_tag, ler_tag, cont, x0, z0, z_lin, kx, kz, etapa_busca, aprox_vals, etapa_aprox, estado_anterior
    global cont, x0, z0, z_lin, kx, kz, etapa_busca, aprox, etapa_aprox, etapa_ideal, estado_anterior, tag_counter
    
    if at_detector is None:
        logger.info("AprilTag detector not available, skipping vision processing")
        return
    
    try:
        import cv2
    except ImportError as e:
        logger.warning(f"Vision dependencies not available: {e}")
        return
    
    while not stop_event.is_set():        
        # Get the latest frame from the queue, if available
        
        try:
            with frame_queue_mutex:
                frame = frame_queue.get_nowait()
        except queue.Empty:
            continue     
        
        try:
            undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
            gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)

            if config.is_autonomous or True: # tirar or 1
                match config.estado:
                    case "ler":
                        tags = at_detector.detect(
                            gray,
                            estimate_tag_pose=True,
                            camera_params=camera_params,
                            tag_size=tag_size,
                        )
                        if tags:
                            for tag in tags:
                                if tag.tag_id == TARGET_TAG_ID[tag_counter]:    
                                    t = tag.pose_t.flatten()
    
                                    x0 += t[0]
                                    z0 += t[2] # ajuste de calibração POSSÍVEL: dividir por 2.8
                                    z_lin += z0 - 0.25 #

                                    kx += tag.pose_R[2, 0]
                                    kz += tag.pose_R[2, 2]

                                    if cont >= 3:
                                        x0 /= 4; z0 /= 4; z_lin /= 4; kx /= 4; kz /= 4

                                        cont = 0
                                       
                                        rho_lin = np.sqrt(x0**2 + z_lin**2)/4
                                        theta_lin = np.arctan2(z_lin, x0)  
                                        theta_k = np.arctan2(kz, kx)       
                                        theta_ef = theta_k - theta_lin    
                                        theta_volta = -(np.pi/2-abs(theta_k)) 

                                        print(f"x0: {x0}, rho': {rho_lin}")
                                        print(f"theta_ef: {theta_ef}, theta_volta: {theta_k}") 
                                        aprox = [f"1 {theta_ef}",f"2 {rho_lin}", f"1 {theta_volta}"] 

                                        #mudar estado = "ideal" para config.is_autonomous = false para desativar o modo firula (pallet autonomo)
                                        if x0 < 0.13 and rho_lin < 0.2: config.estado = "ideal"; estado_anterior = "buscar" # AJUSTAR VALORES ! !
                                        else: config.estado = "aproximar"; etapa_busca = 0;

                                        x0 = z0 = z_lin = kx = kz = 0.0
                                    else:
                                        cont += 1

                        # condição abaixo é a combinação necessária para saber que nenhuma tag foi detectada e as 3 detecções para tirar média já passaram
                        config.estado = estado_anterior if (config.estado == "ler" and cont == 0) else config.estado # AJUSTAR CONDIÇÃO
                    case "buscar":
                        comando = busca[etapa_busca]
                        etapa_busca += 1
                        
                        with command_queue_mutex:
                            command_queue.put(comando) 
                        estado_anterior = "buscar"
                        config.estado = "confirmar"                                       
                        
                        if etapa_busca > 4:
                            etapa_busca = 0
                    case "aproximar":
                        comando = aprox[etapa_aprox]
                        etapa_aprox += 1
                    
                        with command_queue_mutex:
                            command_queue.put(comando)
                        estado_anterior = "aproximar"
                        config.estado = "confirmar"
                        
                        if etapa_aprox > 2:
                            config.estado = "manual"
                            etapa_aprox = 0 
                    case "ideal":
                        comando = ideal[etapa_ideal]
                        etapa_ideal += 1
                        tag_counter = tag_counter + 1 if tag_counter < len(TARGET_TAG_ID) - 1 else 0
                        
                        with command_queue_mutex:
                            command_queue.put(comando) 
                        estado_anterior = "ideal"
                        config.estado = "confirmar" 
                    
                        if etapa_ideal > 4:
                            etapa_ideal = 0
                            #config.estado = "manual"
                            config.is_autonomous = False
                            
                        # Entra no manual até voltar a ser autonomo pelo server
                        config.estado = "manual"
                        etapa_aprox = 0
                    case "confirmar":
                        try:
                            with response_queue_mutex:
                                msg = response_queue.get_nowait()
                        except queue.Empty:
                            msg = ""
                        
                        if msg.startswith("fim modo"): 
                            config.estado = "ler" if estado_anterior != "ideal" else "ideal" 
                                       
        except Exception as e:
            logger.debug(f"Vision processing error: {e}")

async def _websocket_sender():
    """Keep one WebSocket open and stream all frames through it."""
    if not web_socket_url:
        logger.error("WEB_SOCKET_URL is not configured")
        return

    try:
        import websockets
    except ImportError:
        logger.error("The 'websockets' package is not installed")
        return

    reconnect_delay = 1.0

    while not stop_event.is_set():
        try:
            logger.info("Connecting to WebSocket: %s", web_socket_url)

            async with websockets.connect(
                web_socket_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5,
                max_size=None,
            ) as websocket:
                logger.info("WebSocket connected")

                while not stop_event.is_set():
                    try:
                        with ws_queue_mutex:
                            payload = ws_queue.get_nowait()
                    except queue.Empty:
                        await asyncio.sleep(0.01)
                        continue

                    await asyncio.wait_for(
                        websocket.send(payload),
                        timeout=5.0,
                    )

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(
                "WebSocket disconnected (%s). Reconnecting in %.1f seconds",
                exc,
                reconnect_delay,
            )

            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 10.0)
        
async def main():
    serial_writer_thread = start_serial_writer(ser, command_queue, stop_event, command_queue_mutex)
    serial_reader_thread = start_serial_reader(ser, response_queue, stop_event, response_queue_mutex)
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
        serial_writer_thread.join(timeout=1.0)
        serial_reader_thread.join(timeout=1.0)
    
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
