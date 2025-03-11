#!/usr/bin/env python3
"""
server_camera.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  Provides camera configuration and continuous frame capture for the SERVER device.

How it works:
  • Configures the SERVER camera using Picamera2 with appropriate settings.
  • Continuously captures frames in a background thread.
  • Maintains a shared frame buffer with thread safety.
  • Optionally applies frame rate limiting if enabled.

Dependencies:
  • picamera2 – For configuring and capturing camera frames.
      - sudo apt install python3-picamera2
  • opencv (cv2) – For image processing and handling.
      - sudo apt install python3-opencv

Functions:
  • configure_camera() -> Optional[Picamera2]:
      Configures and starts the Picamera2 camera.
  • capture_frames(picam2: Picamera2, update_frame_callback: Callable[[Any], None]) -> None:
      Continuously captures frames and updates the shared buffer.
  • get_latest_frame() -> Optional[Any]:
      Returns a copy of the latest captured frame.

Constants:
  • (None defined in this file)
  
"""

import time
from threading import Lock
from typing import Any, Callable, Optional
from picamera2 import Picamera2
import cv2
from server_configuration import SENSOR_MODE_INDEX, FPS_LIMIT_ENABLED, FPS_LIMIT

_frame_lock: Lock = Lock()
_latest_frame: Optional[Any] = None

def configure_camera() -> Optional[Picamera2]:
    """Configures and starts the Picamera2 camera."""
    picam2: Picamera2 = Picamera2()
    modes = picam2.sensor_modes
    if not modes:
        config = picam2.create_preview_configuration(main={"size": (640, 480)})
        picam2.configure(config)
        picam2.start()
        return picam2
    mode_idx: int = SENSOR_MODE_INDEX if SENSOR_MODE_INDEX < len(modes) else 0
    chosen_mode = modes[mode_idx]
    config = picam2.create_video_configuration(main={"size": chosen_mode.get('size', (640, 480))})
    picam2.configure(config)
    picam2.start()
    return picam2

def capture_frames(picam2: Picamera2, update_frame_callback: Callable[[Any], None]) -> None:
    """Continuously captures frames and updates the shared buffer."""
    global _latest_frame
    while True:
        start_time: float = time.time()
        try:
            frame = picam2.capture_array()
        except Exception:
            try:
                picam2.close()
            except Exception:
                pass
            time.sleep(2)
            try:
                picam2 = configure_camera()  # type: ignore
            except Exception:
                continue
            continue
        with _frame_lock:
            _latest_frame = frame
        update_frame_callback(frame)
        if FPS_LIMIT_ENABLED:
            elapsed: float = time.time()-start_time
            desired_interval: float = 1.0/FPS_LIMIT
            remaining_time: float = desired_interval-elapsed
            if remaining_time>0:
                time.sleep(remaining_time)

def get_latest_frame() -> Optional[Any]:
    """Returns a copy of the latest captured frame."""
    global _latest_frame
    with _frame_lock:
        return _latest_frame.copy() if _latest_frame is not None else None