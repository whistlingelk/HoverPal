#!/usr/bin/env python3
"""
udpu_client_connect.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert released under the MIT License.

Short description:
  Provides a WebSocket-based client on the CLIENT that connects to an unencrypted JPEG frame stream from the SERVER.
  
How it works:
  • Reads candidate IP addresses from "server_ip_address.txt".
  • Attempts a WebSocket connection to each candidate at the designated SERVER_PORT.
  • Upon connection, receives unencrypted frames, decodes them using OpenCV (converting from BGR to RGB), and displays the video stream.
  • Logs connection attempts and handles graceful shutdown.
  • Iterates through candidate IPs until a successful connection is established.

Dependencies:
  • websockets – For asynchronous WebSocket client communication.
      - sudo apt install python3-websockets
  • opencv (cv2) – For decoding JPEG images and displaying video.
      - sudo apt install python3-opencv
  • numpy – For image array processing.
      - sudo apt install python3-numpy
  • client_configuration – Provides configuration constants (SERVER_PORT, PROGRAM_LOG).
  • server_ip_address.txt – Contains candidate server IPs.

Functions:
  • log(msg: str) -> None:
      Logs a message if logging is enabled.
  • load_candidate_ips(filepath: str) -> List[str]:
      Loads candidate IP addresses from file.
  • receive_and_display() -> None:
      Iterates through candidate IPs; attempts WebSocket connection and displays frames.
  • main() -> None:
      Main entry point for the WebSocket client.
"""

import sys
import asyncio
from typing import List

import cv2
import numpy as np
import websockets
from client_configuration import SERVER_PORT, PROGRAM_LOG

# Monkey-patch asyncio functions for compatibility.
_original_lock = asyncio.Lock
def new_lock(*args, **kwargs):
    kwargs.pop('loop', None)
    return _original_lock(*args, **kwargs)
asyncio.Lock = new_lock

_original_sleep = asyncio.sleep
def new_sleep(delay, *args, **kwargs):
    kwargs.pop('loop', None)
    return _original_sleep(delay, *args, **kwargs)
asyncio.sleep = new_sleep

_original_wait_for = asyncio.wait_for
def new_wait_for(awaitable, timeout, *args, **kwargs):
    kwargs.pop('loop', None)
    return _original_wait_for(awaitable, timeout, *args, **kwargs)
asyncio.wait_for = new_wait_for

_original_wait = asyncio.wait
def new_wait(*args, **kwargs):
    if len(args) > 1:
        fs = args[0]
        timeout = args[1]
        args = (fs,)
        kwargs['timeout'] = timeout
    kwargs.pop('loop', None)
    return _original_wait(*args, **kwargs)
asyncio.wait = new_wait

def log(msg: str) -> None:
    """Logs a message if logging is enabled."""
    if PROGRAM_LOG:
        print(msg)

def load_candidate_ips(filepath: str = "server_ip_address.txt") -> List[str]:
    """Loads candidate IP addresses from the specified file."""
    try:
        with open(filepath, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception:
        log("Error loading candidate IPs from server_ip_address.txt")
        return []

async def receive_and_display() -> None:
    """Iterates through candidate IPs; attempts WebSocket connection and displays unencrypted frames."""
    candidate_ips = load_candidate_ips()
    if not candidate_ips:
        log("WebSocket Client: No candidate IP addresses found.")
        return

    connected = False
    for candidate in candidate_ips:
        ws_url = f"ws://{candidate}:{SERVER_PORT}"
        log(f"WebSocket Client: Attempting connection to {ws_url}")

        try:
            async with websockets.connect(ws_url) as websocket:
                connected = True
                log(f"WebSocket Client: Connected to {candidate}")
                while True:
                    try:
                        data = await websocket.recv()
                    except websockets.ConnectionClosed:
                        log("WebSocket Client: Server shutdown.")
                        break

                    # Since the server sends unencrypted JPEG data, use it directly.
                    frame_data = data
                    arr = np.frombuffer(frame_data, dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if img is None:
                        continue

                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    cv2.imshow("WebSocket Unencrypted Feed", img)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                break
        except Exception:
            log(f"WebSocket Client: Connection attempt to {candidate} failed")
            continue

    cv2.destroyAllWindows()
    if not connected:
        log("WebSocket Client: Could not find any server")
    else:
        log("WebSocket Client: Disconnected")

async def run_ws_client() -> None:
    """Runs the asynchronous WebSocket client."""
    await receive_and_display()

def main() -> None:
    """Main entry point for the WebSocket client."""
    try:
        asyncio.run(run_ws_client())
    except KeyboardInterrupt:
        log("WebSocket Client: Disconnected by user")

if __name__ == "__main__":
    main()