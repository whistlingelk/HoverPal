#!/usr/bin/env python3
"""
client_main.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  High-level entry point for the Jetson client, setting up the event loop and
  handling Ctrl+C to shut down gracefully.

How it works:
  • Imports client_core for the actual WebSocket logic and recording pipeline.
  • In main(), runs client_core.jetson_client(), then run_forever() until Ctrl+C.
  • On SIGINT, calls client_core.shutdown_handler() and exits.

Dependencies:
  • client_core, client_configuration
"""

import signal
import sys
import asyncio
from typing import Any

import client_core

loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

def handle_sigint(sig: int, frame: Any) -> None:
    """Schedules shutdown by calling client_core.shutdown_handler()."""
    print("[INFO] Caught Ctrl+C, scheduling shutdown...")
    asyncio.ensure_future(client_core.shutdown_handler())

def main() -> None:
    """Sets up SIGINT, runs the Jetson client logic, and keeps the loop alive."""
    global loop
    signal.signal(signal.SIGINT, handle_sigint)
    asyncio.set_event_loop(loop)

    loop.run_until_complete(client_core.jetson_client_task())
    loop.run_forever()
    loop.close()
    print("Exiting client_main.py")

if __name__ == "__main__":
    main()