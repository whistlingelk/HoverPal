#!/usr/bin/env python3
"""
client_configuration.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  Provides global configuration parameters for the CLIENT device (Jetson or Android),
  including server IP/port, JPEG quality, log settings, and optional IP grabbing logic.

How it works:
  • Runs client_ip_grabber.py to populate 'server_ip_address.txt'.
  • Loads the first valid IP from 'server_ip_address.txt' into SERVER_IP.
  • Defines a single port, a JPEG quality, and a logging flag.
  • No direct encryption references here (WSS can be handled by the app code).

Dependencies:
  • subprocess, sys, os – for file and error handling, running the IP grabber.
  • client_ip_grabber.py – the script that scans the network.

Functions:
  • run_find_server_script(script_path: str) -> None:
      Executes the IP grabber script to update 'server_ip_address.txt'.
  • load_server_ip(filepath: str) -> str:
      Reads the first valid IP from 'server_ip_address.txt'.

Constants:
  • JPEG_QUALITY: int
  • SERVER_IP: str
  • SERVER_PORT: int
  • PROGRAM_LOG: bool
"""

import os
import subprocess
from typing import Optional

def run_find_server_script(script_path: str = "client_ip_grabber.py") -> None:
    """Executes client_ip_grabber.py to update the server IP file."""
    try:
        print(f"[client_configuration] Running {script_path} to find server IP...")
        subprocess.run(["python3", script_path], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to run {script_path}: {e}")

def load_server_ip(filepath: str = "server_ip_address.txt") -> str:
    """Loads the first valid server IP address from file."""
    try:
        with open(filepath, "r") as f:
            for line in f:
                ip: str = line.strip()
                if ip:
                    print(f"[client_configuration] Found IP: {ip}")
                    return ip
        raise Exception("No valid IP address found in the file.")
    except Exception as e:
        raise Exception(f"Failed to load server IP from {filepath}: {e}")

# 1) Attempt to update the server IP file by running the IP grabber script
run_find_server_script()

# 2) Load the newly discovered IP from file
discovered_ip = load_server_ip("server_ip_address.txt")

# Constants
JPEG_QUALITY: int = 95
SERVER_IP: str = discovered_ip  # Use the discovered IP
SERVER_PORT: int = 5000
PROGRAM_LOG: bool = True

print(f"[client_configuration] SERVER_IP={SERVER_IP}, SERVER_PORT={SERVER_PORT}")
