"""
video_processor.py
Receives the WebRTC video stream (as an "answerer"), processes the frames to
detect AprilTags and estimate their pose, and displays the video with bounding boxes.
"""

import asyncio
import logging

import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription

from libs import post_json, wait_for_json, process_frame
from constants.config import SIGNALING_BASE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main entry point. Sets up the WebRTC connection, waits for an offer,
    replies with an answer, and continuously processes video frames.
    """
    # Create the WebRTC peer connection object
    pc = RTCPeerConnection()
    
    # Event to signal when the video processing should stop
    stop_event = asyncio.Event()

    @pc.on("track")
    def on_track(track):
        """
        Callback fired when the remote peer attaches a track.
        """
        async def process_frames():
            try:
                while True:
                    # Receive the raw frame from WebRTC
                    frame = await track.recv()
                    
                    # Convert to BGR format for OpenCV processing
                    image = frame.to_ndarray(format="bgr24")
                    
                    # Process the frame for AprilTags (draws boxes/axes on `image`)
                    image, coords_str = process_frame(image)
                    
                    # Log coordinates if a tag was found
                    if coords_str:
                        logger.info("Coordinates: %s", coords_str)
                    
                    # Show the processed frame on screen
                    cv2.imshow("WebRTC Stream", image)
                    
                    # Wait for 1ms and listen for the 'Esc' key (ASCII 27) to stop
                    if cv2.waitKey(1) & 0xFF == 27:
                        logger.info("Esc pressed, stopping video stream...")
                        stop_event.set()
                        break
            except Exception as e:
                logger.error("Error occurred in process_frames: %s", e, exc_info=True)
                stop_event.set()

        # Start the video consumption process in the background
        asyncio.create_task(process_frames())

    logger.info("Waiting for offer from server...")
    # Fetch the WebRTC offer from the local signaling server
    offer_data = await wait_for_json(f"{SIGNALING_BASE_URL}/offer")
    
    # Apply the remote peer's SDP offer
    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"])
    )

    # Create our WebRTC answer and apply it locally
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    # Post our answer back to the signaling server for the other peer
    await post_json(
        f"{SIGNALING_BASE_URL}/answer",
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
    )

    logger.info("Answer sent. Waiting for video... Press Esc in the video window to stop.")
    
    # Block until the user presses Esc in the OpenCV window
    await stop_event.wait()

    logger.info("Closing connection and windows...")
    cv2.destroyAllWindows()
    await pc.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
    except Exception as e:
        logger.critical("Critical error occurred: %s", e, exc_info=True)