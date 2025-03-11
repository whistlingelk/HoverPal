#!/usr/bin/env python3
"""
udpu_server_connect.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert released under the MIT License.

Short description:
  Provides a WebSocket server on the SERVER that streams unencrypted camera frames.

How it works:
  • Initializes the SERVER camera in a background thread.
  • Captures each frame from the camera in a shared global buffer.
  • A broadcast task encodes each new frame once to JPEG and sends it concurrently to all connected clients.
  • Tracks active clients and logs connection/disconnection events.
  • Uses "WebSocket Server:" as the logging prefix for consistency.

Dependencies:
  • websockets – For asynchronous WebSocket server support.
      - sudo apt install python3-websockets
  • picamera2 – For configuring and capturing camera frames.
      - sudo apt install python3-picamera2
  • opencv (cv2) – For image processing and encoding.
      - sudo apt install python3-opencv
  • server_camera – Provides camera configuration and frame capture.
  • server_configuration – Provides configuration constants (SERVER_IP, SERVER_PORT, PROGRAM_LOG).

Functions:
  • log(msg: str) -> None:
      Logs a message if logging is enabled.
  • start_camera_capture() -> None:
      Starts camera capture in a background thread.
  • register_client(websocket: WebSocketServerProtocol) -> Coroutine:
      Registers an incoming websocket client.
  • unregister_client(websocket: WebSocketServerProtocol) -> Coroutine:
      Unregisters a disconnected websocket client.
  • broadcast_loop() -> Coroutine:
      Encodes the latest frame once and broadcasts it to all active clients.
  • handler(websocket: WebSocketServerProtocol, path: str) -> Coroutine:
      Handles a websocket connection.
  • run_ws_server() -> Coroutine:
      Runs the WebSocket server and the broadcast loop concurrently.
  • shutdown_signal_handler(sig: int, frame: Optional[Any]) -> None:
      Handles shutdown signals gracefully.
  • main() -> None:
      Main entry point for the WebSocket server.
"""

import sys
import os
import time
import threading
import signal
import asyncio
from typing import Set, Optional, Any

import websockets
from websockets import WebSocketServerProtocol
from server_camera import configure_camera, capture_frames, get_latest_frame
from server_configuration import SERVER_IP, SERVER_PORT, PROGRAM_LOG
import cv2

os.environ["LIBCAMERA_LOG_LEVELS"] = "4"

# Global set for connected websocket clients.
connected_clients: Set[WebSocketServerProtocol] = set()
event_loop: Optional[asyncio.AbstractEventLoop] = None

def log(msg: str) -> None:
    """Logs a message if logging is enabled."""
    if PROGRAM_LOG:
        print(msg)

def start_camera_capture() -> None:
    """Starts the camera capture in a background thread."""
    cam = configure_camera()
    if cam is None:
        log("WebSocket Server: Failed to configure camera.")
        return
    threading.Thread(target=capture_frames, args=(cam, lambda frame: None), daemon=True).start()
    time.sleep(2)

async def register_client(websocket: WebSocketServerProtocol) -> None:
    """Registers a connecting websocket client."""
    connected_clients.add(websocket)
    addr = websocket.remote_address
    log(f"WebSocket Server: Client Added: {addr[0]}:{addr[1]}")

async def unregister_client(websocket: WebSocketServerProtocol) -> None:
    """Unregisters a websocket client upon disconnection."""
    connected_clients.discard(websocket)
    addr = websocket.remote_address
    log(f"WebSocket Server: Client Removed: {addr[0]}:{addr[1]}")

async def broadcast_loop() -> None:
    """Continuously encodes the latest frame and broadcasts it to all connected clients."""
    while True:
        frame = get_latest_frame()
        if frame is None:
            await asyncio.sleep(0.1)
            continue
        ret, encoded = cv2.imencode('.jpg', frame)
        if not ret:
            await asyncio.sleep(0.1)
            continue
        jpg_data: bytes = encoded.tobytes()
        if connected_clients:
            await asyncio.gather(*(ws.send(jpg_data) for ws in connected_clients if ws.open), return_exceptions=True)
        await asyncio.sleep(0.033)

async def handler(websocket: WebSocketServerProtocol, path: str) -> None:
    """Handles an incoming websocket connection."""
    await register_client(websocket)
    try:
        await websocket.wait_closed()
    finally:
        await unregister_client(websocket)

async def run_ws_server() -> None:
    """Starts the WebSocket server and broadcast loop concurrently."""
    start_camera_capture()
    log(f"WebSocket Server: Initialized on ws://{SERVER_IP}:{SERVER_PORT}")
    async with websockets.serve(handler, SERVER_IP, SERVER_PORT):
        log("WebSocket Server: Activated")
        log("* End stream with Ctrl+C *")
        await asyncio.gather(asyncio.Future(), broadcast_loop())

def shutdown_signal_handler(sig: int, frame: Optional[Any]) -> None:
    """Handles shutdown signals by stopping the event loop."""
    if connected_clients:
        log("WebSocket Server: Deactivated with clients active")
    else:
        log("WebSocket Server: Deactivated")
    if event_loop is not None:
        event_loop.call_soon_threadsafe(event_loop.stop)

def main() -> None:
    """Main entry point for starting the WebSocket server."""
    global event_loop
    signal.signal(signal.SIGINT, shutdown_signal_handler)
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    try:
        event_loop.run_until_complete(run_ws_server())
    except RuntimeError as ex:
        if "Event loop stopped before Future completed" in str(ex):
            pass
        else:
            raise
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        tasks = asyncio.all_tasks(event_loop)
        for task in tasks:
            task.cancel()
        try:
            event_loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except Exception:
            pass
        event_loop.close()

if __name__ == "__main__":
    main()