#!/usr/bin/env python3
"""
server_commands.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  Contains the function to handle incoming text commands from clients,
  referencing server_core's global states (streaming_active, controlling_client, etc.).

How it works:
  • handle_incoming_messages() reads each line from the WebSocket.
  • Sets streaming_active, recording_active as needed, and calls broadcast_text for updates.
  • Only controlling_client can forcibly stop streaming.

Dependencies:
  • server_core for global state and broadcast_text,
    so we import server_core and manipulate e.g. server_core.streaming_active.
"""

from typing import Any
from websockets.legacy.server import WebSocketServerProtocol

import server_core

async def handle_incoming_messages(websocket: WebSocketServerProtocol) -> None:
    """Reads text commands, modifies server_core states, and broadcasts results."""
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                server_core.log("Ignoring unexpected binary from client.")
                continue

            cmd: str = message.strip().upper()
            server_core.log(f"Received command from client: {cmd}")

            if cmd == "START_LINK":
                server_core.log("Client says START_LINK. No streaming change.")
                # No assignment to controlling_client here.

            elif cmd == "STOP_LINK":
                if websocket == server_core.controlling_client:
                    if server_core.streaming_active or server_core.recording_active:
                        server_core.streaming_active = False
                        server_core.recording_active = False
                        server_core.log("STOP_LINK from controlling client: forcibly stopping streaming/record.")
                    server_core.controlling_client = None

            elif cmd == "START_STREAM":
                if not server_core.streaming_active:
                    server_core.streaming_active = True
                    server_core.controlling_client = websocket
                    server_core.log("Stream started by controlling client.")
                await server_core.broadcast_text("STREAM_STARTED")

            elif cmd == "STOP_STREAM":
                if websocket == server_core.controlling_client and (
                    server_core.streaming_active or server_core.recording_active
                ):
                    if server_core.recording_active:
                        server_core.recording_active = False
                        server_core.log("Recording forcibly stopped with stream stop.")
                        await server_core.broadcast_text("RECORD_STOPPED")

                    server_core.streaming_active = False
                    server_core.log("Stream stopped by controlling client.")
                    server_core.controlling_client = None

                await server_core.broadcast_text("STREAM_STOPPED")

            elif cmd == "START_RECORD":
                if not server_core.streaming_active:
                    server_core.log("START_RECORD but no stream active; ignoring.")
                    await server_core.broadcast_text("RECORD_STOPPED")
                else:
                    # Only controlling client truly "owns" record state,
                    # but we can accept from either if you want.
                    if websocket == server_core.controlling_client:
                        server_core.recording_active = True
                        server_core.log("Recording started by controlling client.")
                    await server_core.broadcast_text("RECORD_STARTED")

            elif cmd == "STOP_RECORD":
                # Only controlling client truly stops record
                if websocket == server_core.controlling_client and server_core.recording_active:
                    server_core.recording_active = False
                    server_core.log("Recording stopped by controlling client.")
                else:
                    server_core.log("STOP_RECORD from non-controlling client or not active.")
                await server_core.broadcast_text("RECORD_STOPPED")

            else:
                server_core.log(f"Unknown command from client: {cmd}")

    except Exception as exc:
        server_core.log(f"Exception in handle_incoming_messages: {exc}")
