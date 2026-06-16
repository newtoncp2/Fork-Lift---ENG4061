import asyncio
import websockets
import cv2
import numpy as np

async def receive_frames(websocket):
    print("Client connected.")
    try:
        async for message in websocket:
            # 1. Convert incoming binary message into a 1D NumPy array
            np_arr = np.frombuffer(message, dtype=np.uint8)
            
            # 2. Decode the compressed image buffer into an OpenCV BGR image
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 3. Process or display your received frame
            cv2.imshow("Received Frame (Binary)", frame)
            
            # Break the loop if 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")

async def main():
    # Start a WebSocket server on localhost port 8765
    async with websockets.serve(receive_frames, "192.168.1.62", 8765):
        print("WebSocket Server running on ws://localhost:8765")
        await asyncio.Future()  # Keep the server running indefinitely

if __name__ == "__main__":
    asyncio.run(main())
