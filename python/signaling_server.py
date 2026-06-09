"""
signaling_server.py
A basic local HTTP server that acts as a signaling channel to exchange
WebRTC SDP offers and answers between the 'raspberry.py' client and 
'video_processor.py' backend.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from threading import Lock

from constants.config import SIGNALING_SERVER_IP, SIGNALING_SERVER_PORT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Global state to hold the current offer and answer
STATE = {"offer": None, "answer": None}
# A lock to ensure thread safety while multiple requests interact with the dict
STATE_LOCK = Lock()


class SignalingHandler(BaseHTTPRequestHandler):
    """
    Handles HTTP GET and POST requests for WebRTC signaling.
    Supports endpoints: /offer, /answer, and /state.
    """
    
    def do_GET(self):
        # Fetch the current SDP offer
        if self.path == "/offer":
            with STATE_LOCK:
                offer = STATE["offer"]
            self._send_json(offer, not_found_message="No offer yet")
            return

        if self.path == "/answer":
            with STATE_LOCK:
                answer = STATE["answer"]
            self._send_json(answer, not_found_message="No answer yet")
            return

        if self.path == "/state":
            with STATE_LOCK:
                current_state = dict(STATE)
            self._send_json(current_state)
            return

        self.send_error(404, "Unknown endpoint")

    def do_POST(self):
        payload = self._read_json()

        if self.path == "/offer":
            with STATE_LOCK:
                STATE["offer"] = payload
                STATE["answer"] = None
            self._send_json({"ok": True})
            return

        if self.path == "/answer":
            with STATE_LOCK:
                STATE["answer"] = payload
            self._send_json({"ok": True})
            return

        self.send_error(404, "Unknown endpoint")

    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s", self.client_address[0], self.log_date_time_string(), format % args)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw_body.decode("utf-8"))

    def _send_json(self, payload, not_found_message=None):
        if payload is None:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": not_found_message or "Not found"}).encode("utf-8"))
            return

        encoded_payload = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded_payload)))
        self.end_headers()
        self.wfile.write(encoded_payload)


def main():
    try:
        server = ThreadingHTTPServer((SIGNALING_SERVER_IP, SIGNALING_SERVER_PORT), SignalingHandler)
        logger.info("Signaling server listening on http://%s:%s", SIGNALING_SERVER_IP, SIGNALING_SERVER_PORT)
        logger.info("Use /offer and /answer endpoints for SDP exchange.")
        server.serve_forever()
    except Exception as e:
        logger.critical("Server failed to start or crashed: %s", e, exc_info=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")