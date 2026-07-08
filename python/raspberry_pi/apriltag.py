'''
    MELHOR VERSÃO POSSÍVEL
'''
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
from scipy.spatial.transform import Rotation as R
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
busca = [f"1 {np.pi/4}\n",f"1 {np.pi/4}\n", f"1 -{np.pi*1.05/4}\n",f"1 -{np.pi*1.05/4}\n", f"1 -{np.pi*1.05/4}\n",f"1 -{np.pi*1.05/4}\n", f"1 {np.pi/4}\n", f"1 {np.pi/4}\n", "2 0.35\n"]

aprox = ["","",""]
ideal = ["3 55",f"2 0.35",f"3 85",f"2 -0.2",f"2 -0.2",f"2 -0.2",f"2 -0.2", f"3 -100"] # AJUSTAR VALORES
etapa_ideal = 0
estado_anterior = "buscar"
x0, z0, z_lin = 0.0, 0.0, 0.0
Rs = []
tmed = np.zeros(3)
cont = 0

#SEARCH_MODE_TIMEOUT = 5.0  # seconds without tag detection before sending search mode command
TARGET_TAG_ID = os.getenv("TARGET_TAG_ID", [0, 8])
tag_counter = 0
try:
    TARGET_TAG_ID = json.loads(TARGET_TAG_ID)
except (ValueError, TypeError):
    logger.warning(f"Invalid TARGET_TAG_ID: {TARGET_TAG_ID}")
    TARGET_TAG_ID = [0, 8]

logger.info("starting mqtt...")
# create and start the mqtt client (connection attempt is non-fatal)
mqtt_client = create_and_start_mqtt(
    mqtt_username,
    mqtt_password,
    mqtt_host,
    mqtt_port,
    on_connect=make_on_connect(["empilhadeira/controle12321"]),
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

def angulo_entre_rad(v1,v2):
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)
    
    produto_escalar = np.dot(v1, v2)
    
    norma_v1 = np.linalg.norm(v1)
    norma_v2 = np.linalg.norm(v2)
    
    cos_angulo = np.clip(produto_escalar / (norma_v1 * norma_v2), -1.0, 1.0)
    
    angulo = np.arccos(cos_angulo)

    cross = np.cross(v2, v1)
    sinal = np.sign(cross[1])

    return sinal*angulo

def media_R(Rs):
    """
    Calcula a média de múltiplas matrizes de rotação usando quaternions.
    """
    quaternions = []
    
    for R_mat in Rs:
        # Converte matriz para quaternion
        r = R.from_matrix(R_mat)
        quat = r.as_quat()  # [x, y, z, w]
        quaternions.append(quat)
    
    # Média dos quaternions (com normalização)
    quat_medio = np.mean(quaternions, axis=0)
    quat_medio = quat_medio / np.linalg.norm(quat_medio)  # Normaliza
    
    # Converte de volta para matriz
    r_medio = R.from_quat(quat_medio)
    return r_medio.as_matrix()

def _vision_worker():
    """Process frames for tags if detector is available."""
    #global last_tag, ler_tag, cont, x0, z0, z_lin, kx, kz, etapa_busca, aprox_vals, etapa_aprox, estado, estado_anterior
    global cont, x0, z0, z_lin, tmed, Rmed, aprox, etapa_ideal, estado_anterior, tag_counter
    
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

            if config.is_autonomous:  # tirar or 1
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

                                    with response_queue_mutex:
                                        while not response_queue.empty():
                                            try:
                                                response_queue.get_nowait()
                                            except:
                                                break
                                    
                                    print("TARGET_ID:" + str(TARGET_TAG_ID[tag_counter]));
                                    r = np.asarray(tag.pose_R, dtype=float)        # (3, 3)
                                    t = np.asarray(tag.pose_t, dtype=float).ravel()  # (3,)
                                    tmed += t
                                    Rs.append(r)
                
                                    if cont >= 5:
                                        tmed /= 6
                                        Rmed = media_R(Rs)
                                        
                                        cont = 0
                                        
                                        n_cam_cam_space = np.array([0, 0, 1])
                                        
                                        '''VETOR normal da camera no espaço da tag'''
                                        n_cam_tag_space = Rmed.T @ n_cam_cam_space
                                        n_cam_tag_space[1] = 0
                                        if n_cam_tag_space[2] > 0: n_cam_tag_space *= -1

                                        '''PONTO da posição da camera no ESPAÇO DA TAG'''
                                        posicao_camera = Rmed.T @ tmed   
                                        
                                        posicao_camera[1] = 0
                                        posicao_camera[2] *= -1
                                        x0 = posicao_camera[0]
                                        z0 = -posicao_camera[2] # SE Z0 CHEGA COMO NEGATIVO, z0 = -posicao_camera[2]
                                        '''robo para 0.15 m à frente da câmera'''
                                        
                                        z_lin =  z0 + 0.3  

                                        rho_lin = (x0**2 + z_lin**2)**0.5

                                        w = np.array([0.0, 0.0, 0.3]) - np.array(posicao_camera)

                                        theta_lin = angulo_entre_rad(n_cam_tag_space,w) if x0 > 0 else angulo_entre_rad(w, n_cam_tag_space)
                                        theta_volta = angulo_entre_rad([0,0,-1], w) if x0 < 0 else -angulo_entre_rad(w, [0,0,-1])
                                        
                                        #theta_lin = np.arctan2(n_cam_tag_space, w)
                                        #theta_volta = np.(w)
                                        print(f"x_t : {tmed[0]} , z_t : {tmed[2]}") 
                                        print(f"w: {w}, n_cam: {n_cam_tag_space}") 
                                        print(f"x0: {x0}, z0: {z0}, z': {z_lin}, rho_lin {rho_lin}")
                                        print(f"theta_lin: {theta_lin}, theta_volta: {theta_volta}") 
                                        aprox = [f"1 {theta_lin}",f"2 {abs(rho_lin)}", f"1 {theta_volta}"]

                                        _, pitch, _ = R.from_matrix(Rmed).as_euler('zyx', degrees=True)
                                        print(pitch)
                                        
                                        distancia = np.linalg.norm(tmed)

                                        if abs(pitch) < 3 and rho_lin < 0.28: config.estado = "ideal"; estado_anterior = "buscar" # AJUSTAR RHO_LIN ! !
                                        else: config.estado = "aproximar"; config.etapa_busca = 0;

                                        tmed = np.zeros(3); Rs.clear()
                                    else:
                                        cont += 1

                        # condição abaixo é a combinação necessária para saber que nenhuma tag foi detectada e as 3 detecções para tirar média já passaram
                        config.estado = estado_anterior if (config.estado == "ler" and cont == 0) else config.estado
                        #if config.estado == "aproximar" and etapa_aprox != 0: config.estado = "aproximar"
                    case "buscar":
                        comando = busca[config.etapa_busca]
                        config.etapa_busca += 1
                        
                        with command_queue_mutex:
                            command_queue.put(comando) 
                        estado_anterior = "buscar"
                        config.estado = "confirmar"                                       
                        
                        if config.etapa_busca > 8:
                            config.etapa_busca = 0
                    case "aproximar":
                        comando = aprox[config.etapa_aprox]
                        config.etapa_aprox += 1

                        with command_queue_mutex:
                            command_queue.put(comando)
                        estado_anterior = "aproximar"
                        config.estado = "confirmar"
                        
                        if config.etapa_aprox > 2:
                            aprox.clear()
                            config.estado = "ler"
                            estado_anterior = "buscar"
                            config.etapa_aprox = 0
                            etapa_busca = 0 
                    case "ideal":
                        print("ideal")
                        comando = ideal[etapa_ideal]
                        etapa_ideal += 1
                       
                        with command_queue_mutex:
                            command_queue.put(comando) 
                        estado_anterior = "ideal"
                        config.estado = "confirmar" 
                    
                        if etapa_ideal > 7:
                            tag_counter += 1 if tag_counter < len(TARGET_TAG_ID) else 0
                            etapa_ideal = 0
                            config.estado = "ler"
                            estado_anterior = "buscar"
                            config.is_autonomous = False
                    case "confirmar":
                        try:
                            with response_queue_mutex:
                                msg = response_queue.get_nowait()
                        except:
                            msg = ""

                        if msg.startswith("fim modo"):
                            msg = "" 
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
