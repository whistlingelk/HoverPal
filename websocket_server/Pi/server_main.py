#!/usr/bin/env python3
"""
server_main.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  High-level entry point for the Pi server. Sets up the event loop, starts the
  WebSocket server, and handles graceful shutdown on Ctrl+C.

How it works:
  • Imports server_core for camera capture, broadcast logic, etc.
  • Imports server_commands for command handling.
  • Defines a handler(...) function for each incoming connection,
    which registers/unregisters clients and routes messages to server_commands.
  • On SIGINT, stops the event loop gracefully.

Dependencies:
  • websockets, server_core, server_commands, server_configuration
"""

import signal
import asyncio
from typing import Any

import websockets
from websockets.legacy.server import WebSocketServerProtocol

import server_core
import server_commands
from server_configuration import SERVER_IP, SERVER_PORT, PROGRAM_LOG

event_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

async def handler(websocket: WebSocketServerProtocol, path: str) -> None:
    """
    Handles a new client connection: register, process commands,
    and unregister on disconnect.
    """
    await server_core.register_client(websocket)
    try:
        await server_commands.handle_incoming_messages(websocket)
    finally:
        await server_core.unregister_client(websocket)

async def run_ws_server() -> None:
    """
    Initiates camera capture, starts the WebSocket server, and
    runs the broadcast loop concurrently.
    """
    server_core.start_camera_capture()
    server_core.log(f"WebSocket Server: Initialized on ws://{SERVER_IP}:{SERVER_PORT}")

    async with websockets.serve(handler, SERVER_IP, SERVER_PORT):
        server_core.log("WebSocket Server: Activated (Ctrl+C to stop).")
        await asyncio.gather(asyncio.Future(), server_core.broadcast_loop())

def shutdown_signal_handler(sig: int, frame: Any) -> None:
    """Stops the event loop on SIGINT."""
    if server_core.connected_clients:
        server_core.log("WebSocket Server: Deactivated with clients connected.")
    else:
        server_core.log("WebSocket Server: Deactivated (no active clients).")

    event_loop.stop()

def main() -> None:
    """Sets up the SIGINT handler, runs run_ws_server(), and gracefully closes on exit."""
    global event_loop
    signal.signal(signal.SIGINT, shutdown_signal_handler)
    asyncio.set_event_loop(event_loop)
    try:
        event_loop.run_until_complete(run_ws_server())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        tasks = asyncio.all_tasks(event_loop)
        for tsk in tasks:
            tsk.cancel()
        try:
            event_loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except Exception:
            pass
        event_loop.close()

if __name__ == "__main__":
    main()

