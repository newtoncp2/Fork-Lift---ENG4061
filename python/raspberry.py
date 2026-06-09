"""
raspberry.py
Captures the camera feed using MediaPlayer and sends it via WebRTC (as an "offerer").
This script is designed to run on the Edge device (e.g., Raspberry Pi).
"""

import asyncio
import logging
import msvcrt

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer

from libs import post_json, wait_for_json
from constants.config import SIGNALING_BASE_URL, CAMERA_NAME, CAMERA_RESOLUTION, MEDIA_PLAYER_FORMAT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main entry point for the camera sender. Initializes the peer connection,
    starts recording the webcam, and publishes its SDP offer for the backend.
    """
    pc = RTCPeerConnection()
    
    # Configure the media player to capture the local webcam
    player = MediaPlayer(
        f"video={CAMERA_NAME}",
        format=MEDIA_PLAYER_FORMAT,
        options={"video_size": CAMERA_RESOLUTION},
    )

    try:
        # Attach the video stream to our connection
        pc.addTrack(player.video)
        logger.info("Video track attached.")

        # Create our SDP offer and apply it locally
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        # Post our offer to the signaling server so the receiver can fetch it
        await post_json(
            f"{SIGNALING_BASE_URL}/offer",
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        )
        logger.info("Offer sent. Waiting for answer...")

        # Poll the signaling server until the receiver posts its answer
        answer_data = await wait_for_json(f"{SIGNALING_BASE_URL}/answer")
        
        # Apply the remote peer's SDP answer
        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        )
        logger.info("Peer connected. Press Esc to stop.")

        # Keep running until 'Esc' is pressed in the terminal window
        while True:
            if msvcrt.kbhit():
                # Read the key press
                key = msvcrt.getch()
                # If 'Esc' (ASCII 27 / \x1b) is pressed, exit the infinite loop
                if key == b"\x1b":
                    logger.info("Esc pressed, stopping...")
                    break
            # Add a small delay to prevent this loop from burning 100% CPU
            await asyncio.sleep(0.05)
            
    except Exception as e:
        logger.error("An error occurred: %s", e, exc_info=True)
    finally:
        # Cleanup: stop the camera hardware and close the connection
        if hasattr(player, "stop"):
            player.stop()
        await pc.close()
        logger.info("Connection stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.critical("Critical error occurred: %s", e, exc_info=True)

