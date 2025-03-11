#!/usr/bin/env python3
"""
server_core.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  Core logic for the Pi server, including camera setup, global states,
  broadcasting frames, and basic logging.

How it works:
  • start_camera_capture() spawns a background thread from server_camera.
  • broadcast_loop() continuously encodes frames to JPEG and sends to connected clients
    if streaming_active == True.
  • Tracks controlling_client so that only that client's departure or STOP_STREAM halts streaming.
  • register_client/unregister_client handle connected_clients set.

Dependencies:
  • server_configuration for FPS_LIMIT, PROGRAM_LOG, etc.
  • server_camera for camera config, frame capture.
  • websockets for WebSocketServerProtocol references.
"""

import time
import threading
import asyncio
from typing import Set, Optional

import cv2
from websockets.legacy.server import WebSocketServerProtocol

import server_camera
import server_configuration as config

connected_clients: Set[WebSocketServerProtocol] = set()
controlling_client: Optional[WebSocketServerProtocol] = None

streaming_active: bool = False
recording_active: bool = False

def start_camera_capture() -> None:
    """Launches camera capture in a background thread."""
    cam = server_camera.configure_camera()
    if cam is None:
        log("WebSocket Server: Failed to configure camera.")
        return
    threading.Thread(target=server_camera.capture_frames, args=(cam, lambda f: None), daemon=True).start()
    time.sleep(2)

async def broadcast_loop() -> None:
    """Continuously sends frames to all open clients if streaming_active is True."""
    global streaming_active
    while True:
        if not streaming_active:
            await asyncio.sleep(0.1)
            continue

        frame = server_camera.get_latest_frame()
        if frame is None:
            await asyncio.sleep(0.1)
            continue

        start_time = time.time()

        # Encode with specified JPEG quality
        ret, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY])
        if not ret:
            await asyncio.sleep(0.1)
            continue

        jpg_data: bytes = encoded.tobytes()

        # Broadcast to all open clients
        if connected_clients:
            tasks = []
            for ws in connected_clients:
                if ws.open:
                    tasks.append(ws.send(jpg_data))
            await asyncio.gather(*tasks, return_exceptions=True)

        if config.FPS_LIMIT_ENABLED:
            elapsed = time.time() - start_time
            desired_interval = 1.0 / float(config.FPS_LIMIT)
            sleep_time = desired_interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        else:
            # ~30 FPS if no limit
            await asyncio.sleep(0.033)

def log(msg: str) -> None:
    """Logs a message if config.PROGRAM_LOG is True."""
    if config.PROGRAM_LOG:
        print(msg)

async def broadcast_text(message: str) -> None:
    """Sends a text message to all open clients."""
    if not connected_clients:
        return
    tasks = []
    for ws in connected_clients:
        if ws.open:
            tasks.append(ws.send(message))
    await asyncio.gather(*tasks, return_exceptions=True)

async def register_client(websocket: WebSocketServerProtocol) -> None:
    """Adds the new client, logs address and active count."""
    connected_clients.add(websocket)
    addr = websocket.remote_address
    log(f"Client connected: {addr}")
    log(f"Active clients: {len(connected_clients)}")

async def unregister_client(websocket: WebSocketServerProtocol) -> None:
    """
    Removes the client from connected_clients.
    If it was controlling_client, forcibly stop streaming/recording.
    """
    global controlling_client, streaming_active, recording_active

    addr = websocket.remote_address
    log(f"Client disconnected: {addr}")

    if websocket == controlling_client:
        if streaming_active or recording_active:
            streaming_active = False
            recording_active = False
            log("Controlling client disconnected; forcibly stopped stream/record.")
        controlling_client = None

    connected_clients.discard(websocket)
    log(f"Client removed. Active clients: {len(connected_clients)}")

               