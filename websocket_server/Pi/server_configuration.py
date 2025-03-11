#!/usr/bin/env python3
"""
server_configuration.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  Provides global configuration parameters for the SERVER device (Raspberry Pi),
  including sensor mode, optional FPS limiting, JPEG quality, and network settings.

How it works:
  • Defines constants for sensor configuration, frame capture, and network parameters.
  • If FPS_LIMIT_ENABLED is True, the server can enforce a maximum FPS in broadcasting frames.
  • Does not include any encryption references.

Dependencies:
  • None (pure constants).

Constants:
  • SENSOR_MODE_INDEX: int
  • FPS_LIMIT_ENABLED: bool
  • FPS_LIMIT: int
  • JPEG_QUALITY: int
  • SERVER_IP: str
  • SERVER_PORT: int
  • PROGRAM_LOG: bool
"""

SENSOR_MODE_INDEX: int = 4        # Preferred sensor mode index (0-7)
FPS_LIMIT_ENABLED: bool = False   # Flag to enable frame rate limiting
FPS_LIMIT: int = 30              # Maximum FPS if limiting is enabled
JPEG_QUALITY: int = 95           # JPEG quality value
SERVER_IP: str = "0.0.0.0"       # SERVER binds to all interfaces
SERVER_PORT: int = 5000          # Port for the SERVER
PROGRAM_LOG: bool = True         # Enable logging if True
