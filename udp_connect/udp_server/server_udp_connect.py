#!/usr/bin/env python3
"""
server_udp_connect.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert released under the MIT License.

Short description:
  Provides a WebSocket server on the SERVER that streams encrypted camera frames.

How it works:
  • Initializes the SERVER camera in a background thread.
  • Encrypts each captured frame using encrypt_jpg from server_encryption and streams it to WebSocket clients.
  • Tracks active clients and logs connection/disconnection events.
  • Uses "WebSocket Server:" as the logging prefix for consistency.

Dependencies:
  • websockets – For asynchronous WebSocket server support.
      - sudo apt install python3-websockets
  • picamera2 – For configuring and capturing camera frames.
      - sudo apt install python3-picamera2
  • opencv (cv2) – For image processing and encoding.
      - sudo apt install python3-opencv
  • pycryptodome – For encryption.
      - sudo apt install python3-pycryptodome
  • server_camera – Provides camera configuration and frame capture.
  • server_encryption – Provides encrypt_jpg for encryption.
  • server_configuration – Provides configuration constants (SERVER_IP, SERVER_PORT, PROGRAM_LOG).
  
Functions:
  • log(msg: str) -> None:
      Logs a message if logging is enabled.
  • start_camera_capture() -> None:
      Starts camera capture in a background thread.
  • stream_encrypted_feed(websocket: WebSocketServerProtocol, path: str) -> None:
      Streams encrypted frames to a connected client.
  • run_ws_server() -> None:
      Runs the WebSocket server indefinitely.
  • shutdown_signal_handler(sig: int, frame: Optional[Any]) -> None:
      Handles shutdown signals gracefully.
  • main() -> None:
      Main entry point for the WebSocket server.

Constants:
  • (None defined in this file)

"""

import sys
import os
import time
import threading
import signal
import asyncio
from typing import Set, Tuple, Optional, Any

import websockets
from websockets import WebSocketServerProtocol
from server_camera import configure_camera, capture_frames, get_latest_frame
from server_encryption import encrypt_jpg
from server_configuration import SERVER_IP, SERVER_PORT, PROGRAM_LOG

os.environ['LIBCAMERA_LOG_LEVELS'] = '4'

active_clients: Set[Tuple[str, int]] = set()
event_loop: Optional[asyncio.AbstractEventLoop] = None

def log(msg: str) -> None:
    """Logs a message if logging is enabled."""
    if PROGRAM_LOG:
        print(msg)

def start_camera_capture() -> None:
    """Starts camera capture in a background thread."""
    cam: Optional[Any] = configure_camera()
    if cam is None:
        log("WebSocket Server: Failed to configure camera.")
        return
    threading.Thread(target=capture_frames, args=(cam, lambda frame: None), daemon=True).start()
    time.sleep(2)

async def stream_encrypted_feed(websocket: WebSocketServerProtocol, path: str) -> None:
    """Streams encrypted frames to a connected client."""
    client: Tuple[str, int] = websocket.remote_address  # type: ignore
    active_clients.add(client)
    log(f"WebSocket Server: Client Added: {client[0]}:{client[1]}")
    try:
        while True:
            frame = get_latest_frame()
            if frame is None:
                await asyncio.sleep(0.1)
                continue
            chunk: Optional[bytes] = encrypt_jpg(frame)
            if not chunk:
                await asyncio.sleep(0.1)
                continue
            await websocket.send(chunk)
            await asyncio.sleep(0)
    except websockets.ConnectionClosed:
        log("WebSocket Server: Client disconnected")
    except Exception as e:
        log(f"WebSocket Server: Error: {e}")
    finally:
        active_clients.discard(client)
        log(f"WebSocket Server: Client Removed: {client[0]}:{client[1]}")

async def run_ws_server() -> None:
    """Runs the WebSocket server indefinitely."""
    start_camera_capture()
    log(f"WebSocket Server: Initialized on ws://{SERVER_IP}:{SERVER_PORT}")
    async with websockets.serve(stream_encrypted_feed, SERVER_IP, SERVER_PORT):
        log("WebSocket Server: Activated")
        log("* End stream with Ctrl+C *")
        await asyncio.Future()

def shutdown_signal_handler(sig: int, frame: Optional[Any]) -> None:
    """Handles shutdown signals gracefully."""
    if active_clients:
        log("WebSocket Server: Deactivated with clients active")
    else:
        log("WebSocket Server: Deactivated")
    if event_loop is not None:
        event_loop.call_soon_threadsafe(event_loop.stop)

def main() -> None:
    """Main entry point for the WebSocket server."""
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