#!/usr/bin/env python3
"""
client_encryption.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert released under the MIT License.

Short description:
  Provides encryption and decryption functions for the CLIENT.
  Implements a generic decryption routine (decrypt_data) for encrypted binary data using DATA_KEY.

How it works:
  • decrypt_data implements decryption for data in the format:
    [4-byte little-endian ciphertext length][12-byte nonce][16-byte tag][ciphertext].
  • The function obtains the data encryption key (DATA_KEY) from client_configuration.

Dependencies:
  • pycryptodome – For ChaCha20-Poly1305 decryption.
      - sudo apt install python3-pycryptodome
  • client_configuration – Provides DATA_KEY.

Functions:
  • decrypt_data(data: bytes) -> Optional[bytes]:
      Decrypts encrypted binary data using ChaCha20-Poly1305 and DATA_KEY.

Constants:
  • (None defined in this file)
"""

import struct
from Cryptodome.Cipher import ChaCha20_Poly1305
from typing import Optional
from client_configuration import DATA_KEY

def decrypt_data(data: bytes) -> Optional[bytes]:
    """Decrypts encrypted binary data using ChaCha20-Poly1305 and DATA_KEY."""
    if len(data) < 4+12+16:
        return None
    ciphertext_len = struct.unpack("<I", data[:4])[0]
    if len(data) < 4+12+16+ciphertext_len:
        return None
    nonce = data[4:4+12]
    tag = data[4+12:4+12+16]
    ciphertext = data[4+12+16:4+12+16+ciphertext_len]
    try:
        cipher = ChaCha20_Poly1305.new(key=DATA_KEY, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext
    except Exception:
        print("Decryption failed")
        return None