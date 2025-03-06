#!/usr/bin/env python3
"""
server_encryption.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert released under the MIT License.

Short description:
  Provides encryption functions for the SERVER.
  Implements a generic encryption routine (encrypt_data) and an encrypt_jpg function for encrypting JPEG data using DATA_KEY.

How it works:
  • encrypt_data encodes plain binary data with ChaCha20-Poly1305 into the format:
    [4-byte little-endian ciphertext length][12-byte nonce][16-byte tag][ciphertext].
  • encrypt_jpg converts a frame to JPEG using OpenCV, then encrypts it using encrypt_data.
  • DATA_KEY is imported from server_configuration.

Dependencies:
  • opencv (cv2) – For converting frames to JPEG images.
      - sudo apt install python3-opencv
  • pycryptodome – For ChaCha20-Poly1305 encryption.
      - sudo apt install python3-pycryptodome
  • server_configuration – Provides DATA_KEY.

Functions:
  • encrypt_data(data: bytes, data_key: bytes) -> Optional[bytes]:
      Encrypts generic binary data using ChaCha20-Poly1305 and DATA_KEY.
  • encrypt_jpg(frame: Any) -> Optional[bytes]:
      Converts a frame to JPEG and encrypts it using encrypt_data with DATA_KEY.

Constants:
  • (None defined in this file)
"""

import cv2
import struct
from typing import Any, Optional
from Cryptodome.Cipher import ChaCha20_Poly1305
from Cryptodome.Random import get_random_bytes
from server_configuration import DATA_KEY

def encrypt_data(data: bytes, data_key: bytes) -> Optional[bytes]:
    """Encrypts generic binary data using ChaCha20-Poly1305 and DATA_KEY."""
    nonce = get_random_bytes(12)
    cipher = ChaCha20_Poly1305.new(key=data_key, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return struct.pack("<I", len(ciphertext)) + nonce + tag + ciphertext

def encrypt_jpg(frame: Any) -> Optional[bytes]:
    """Converts a frame to JPEG and encrypts it using encrypt_data with DATA_KEY."""
    ret, encoded = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    plaintext: bytes = encoded.tobytes()
    return encrypt_data(plaintext, DATA_KEY)