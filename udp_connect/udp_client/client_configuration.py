#!/usr/bin/env python3
"""
client_configuration.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert released under the MIT License.

Short description:
  Provides global configuration parameters for the CLIENT encrypted video streaming system.
  Loads encryption keys and candidate server IP addresses.

How it works:
  • Loads a 32-character data encryption key from "server_data_encryption_key.txt".
  • Executes client_ip_grabber.py to update "server_ip_address.txt" and then loads the first candidate.
  
Dependencies:
  • subprocess – For executing the IP grabber script.
  • sys, os – For file and error handling.

Functions:
  • load_data_encryption_key(filepath: str) -> bytes:
      Loads the data encryption key from a given file.
  • run_find_server_script(script_path: str) -> None:
      Executes client_ip_grabber.py to update the server IP file.
  • load_server_ip(filepath: str) -> str:
      Loads the first valid server IP address from file.
  
Constants:
  • JPEG_QUALITY: int
  • SERVER_IP: str
  • SERVER_PORT: int
  • PROGRAM_LOG: bool
  • DATA_KEY: bytes
"""

import subprocess
import sys
import os
from typing import Any

def load_data_encryption_key(filepath: str = "server_data_encryption_key.txt") -> bytes:
    """Loads the data encryption key from a given file."""
    try:
        with open(filepath, "r") as f:
            key_str: str = f.read().strip()
            if len(key_str) != 32:
                raise ValueError("Data encryption key must be 32 characters long.")
            return key_str.encode("utf-8")
    except Exception as e:
        raise Exception(f"Failed to load data encryption key from {filepath}: {e}")

def run_find_server_script(script_path: str = "client_ip_grabber.py") -> None:
    """Executes client_ip_grabber.py to update the server IP file."""
    try:
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
                    return ip
        raise Exception("No valid IP address found in the file.")
    except Exception as e:
        raise Exception(f"Failed to load server IP from {filepath}: {e}")

JPEG_QUALITY: int = 95

run_find_server_script()  # Update the server IP address file.
SERVER_IP: str = load_server_ip()  # Load the server IP.
SERVER_PORT: int = 5000         # Port shared by both CLIENT and SERVER.
PROGRAM_LOG: bool = True

DATA_KEY: bytes = load_data_encryption_key()  # Load the data encryption key.