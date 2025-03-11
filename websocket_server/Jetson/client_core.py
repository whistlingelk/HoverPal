#!/usr/bin/env python3
"""
client_core.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  Core logic for the Jetson WebSocket client: connecting to the Pi,
  capturing frames upon RECORD_STARTED, color-swapping them post-recording,
  and producing an MKV via ffmpeg.

How it works:
  • jetson_client_task() attempts to connect to the server, sends START_LINK,
    and processes messages (binary frames, text commands).
  • If record_active=True, frames are saved to disk. On RECORD_STOPPED, we
    color-correct and run ffmpeg, then remove the folder.
  • shutdown_handler() forcibly closes the socket and exits on Ctrl+C.

Dependencies:
  • websockets, opencv, ffmpeg, client_configuration
"""

import os
import sys
import time
import asyncio
import datetime
import pathlib
import shutil
import subprocess
from typing import Optional

import cv2
import websockets
from websockets import WebSocketClientProtocol

import client_configuration as config

ws_connection: Optional[WebSocketClientProtocol] = None
record_active: bool = False
record_dir: pathlib.Path = pathlib.Path()
first_frame_timestamp: Optional[float] = None

async def jetson_client_task() -> None:
    """Tries connecting to the Pi, sends START_LINK, then processes frames/commands."""
    global ws_connection
    uri = f"ws://{config.SERVER_IP}:{config.SERVER_PORT}"
    print(f"Connecting to server at {uri} ...")

    try:
        async with websockets.connect(uri) as websocket:
            ws_connection = websocket
            print("Connected. Sending START_LINK command...")
            await websocket.send("START_LINK")

            async for message in websocket:
                if isinstance(message, bytes):
                    await handle_incoming_frame(message)
                else:
                    await handle_incoming_text(message)
    except Exception as exc:
        print(f"[ERROR] WebSocket exception: {exc}")

async def handle_incoming_frame(frame_bytes: bytes) -> None:
    """Saves frames as .jpg if record_active==True."""
    global record_active, record_dir, first_frame_timestamp
    if not record_active:
        return

    if first_frame_timestamp is None:
        first_frame_timestamp = time.time()
        print(f"[INFO] First frame timestamp set to {first_frame_timestamp:.3f}")

    now_ts = time.time()
    filename = f"{now_ts:.6f}.jpg"
    filepath = record_dir / filename
    try:
        with open(filepath, "wb") as fh:
            fh.write(frame_bytes)
    except Exception as e:
        print(f"[ERROR] writing frame {filepath}: {e}")

async def handle_incoming_text(text: str) -> None:
    """Parses text commands (RECORD_STARTED/STOPPED) to manage local capture pipeline."""
    global record_active, record_dir, first_frame_timestamp

    print(f"Received text: {text}")

    if text == "RECORD_STARTED":
        videos_dir = pathlib.Path("videos")
        videos_dir.mkdir(exist_ok=True)

        dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        record_dir = videos_dir / f"record_temp_{dt_str}"
        record_dir.mkdir(exist_ok=True)

        record_active = True
        first_frame_timestamp = None
        print(f"[INFO] RECORD_STARTED -> storing frames in {record_dir}")

    elif text == "RECORD_STOPPED":
        if record_active:
            record_active = False
            print("[INFO] RECORD_STOPPED -> post-processing frames...")

            color_correct_folder(record_dir)
            await finalize_recording()
            remove_record_dir(record_dir)

            first_frame_timestamp = None
            record_dir = pathlib.Path()
        else:
            print("[INFO] RECORD_STOPPED but we weren't recording? ignoring.")

async def finalize_recording() -> None:
    """Encodes frames in record_dir into an MKV via ffmpeg, naming after first_frame_timestamp."""
    global record_dir, first_frame_timestamp

    frames = list(record_dir.glob("*.jpg"))
    if not frames:
        print("[WARN] No frames to encode. Skipping ffmpeg.")
        return

    if first_frame_timestamp is None:
        first_frame_timestamp = time.time()

    dt_obj = datetime.datetime.fromtimestamp(first_frame_timestamp)
    dt_str = dt_obj.strftime("%Y%m%d_%H%M%S")
    final_mkv = record_dir.parent / f"VIDEO_{dt_str}.mkv"

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", "30",
        "-pattern_type", "glob",
        "-i", str(record_dir / "*.jpg"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(final_mkv)
    ]
    print(f"[INFO] Running ffmpeg to produce {final_mkv}")
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode == 0:
        print(f"[INFO] ffmpeg succeeded, file at {final_mkv}")
    else:
        print(f"[ERROR] ffmpeg failed with code {proc.returncode}")

def color_correct_folder(folder: pathlib.Path) -> None:
    """Swaps red/blue channels in each .jpg by decoding with OpenCV and overwriting."""
    print(f"[INFO] Swapping R/B on frames in {folder} ...")
    count = 0
    for jpg_path in folder.glob("*.jpg"):
        try:
            img_bgr = cv2.imread(str(jpg_path), cv2.IMREAD_UNCHANGED)
            if img_bgr is None:
                print(f"[WARN] Could not decode {jpg_path}, skipping.")
                continue
            img_rgb = img_bgr[..., ::-1]
            cv2.imwrite(str(jpg_path), img_rgb)
            count += 1
        except Exception as exc:
            print(f"[ERROR] color_correct_folder {jpg_path}: {exc}")
    print(f"[INFO] Color-corrected {count} frames in {folder}")

def remove_record_dir(folder: pathlib.Path) -> None:
    """Removes the entire recording folder after finalizing the MKV."""
    try:
        shutil.rmtree(folder)
        print(f"[INFO] Removed folder {folder}")
    except Exception as exc:
        print(f"[ERROR] remove_record_dir {folder}: {exc}")

async def shutdown_handler() -> None:
    """Sends STOP_LINK, closes socket, forcibly exits."""
    global ws_connection
    if ws_connection is not None:
        try:
            print("[INFO] Sending STOP_LINK before disconnecting...")
            await ws_connection.send("STOP_LINK")
            await ws_connection.close()
            print("[INFO] Closed WebSocket.")
        except Exception as exc:
            print(f"[ERROR] closing WebSocket: {exc}")

    print("[INFO] Exiting now.")
    sys.exit(0)