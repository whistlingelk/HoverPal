#!/usr/bin/env python3
"""
server_configuration.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert released under the MIT License.

Short description:
  Provides global configuration parameters for the SERVER encrypted video streaming system.
  Loads encryption keys and defines network and camera constants.

How it works:
  • Loads a 32-character data encryption key from "server_data_encryption_key.txt".
  • Defines constants for sensor configuration, frame capture, and network settings.

Dependencies:
  • os – For file operations.

Functions:
  • load_data_encryption_key(filepath: str) -> bytes:
      Loads the data encryption key from a file.
  
Constants:
  • SENSOR_MODE_INDEX: int
  • FPS_LIMIT_ENABLED: bool
  • FPS_LIMIT: int
  • JPEG_QUALITY: int
  • SERVER_IP: str
  • SERVER_PORT: int
  • PROGRAM_LOG: bool
  • DATA_KEY: bytes
"""

import os
from typing import Any

def load_data_encryption_key(filepath: str = "server_data_encryption_key.txt") -> bytes:
    """Loads the data encryption key from a file."""
    try:
        with open(filepath, "r") as f:
            key_str: str = f.read().strip()
            if len(key_str) != 32:
                raise ValueError("Data encryption key must be 32 characters long.")
            return key_str.encode("utf-8")
    except Exception as e:
        raise Exception(f"Failed to load data encryption key from {filepath}: {e}")

SENSOR_MODE_INDEX: int = 4            # Preferred sensor mode index (0-7)
FPS_LIMIT_ENABLED: bool = False       # Flag to enable frame rate limiting
FPS_LIMIT: int = 30                   # Maximum FPS if limiting is enabled
JPEG_QUALITY: int = 95                # JPEG quality value
SERVER_IP: str = "0.0.0.0"             # SERVER binds to all interfaces
SERVER_PORT: int = 5000               # Port for the SERVER
PROGRAM_LOG: bool = True              # Enable logging if True

DATA_KEY: bytes = load_data_encryption_key()  # Load the data encryption key.