#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:50
# @File     : ffmpeg_service.py
# @Desc     : FFmpeg rendering helpers.

import subprocess
from pathlib import Path

from app.core.config import settings


def check_ffmpeg() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [settings.ffmpeg_bin, "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr or "").splitlines()
    return result.returncode == 0, output[0] if output else "ffmpeg returned no output"


def render_placeholder_video(output_path: Path, title: str, duration_seconds: int = 6) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not settings.enable_real_ffmpeg:
        output_path.write_bytes(b"hours24 mvp placeholder video\n")
        return

    safe_title = title.replace(":", " ").replace("\\", " ").replace("/", " ")[:40]
    command = [
        settings.ffmpeg_bin,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x111827:s=1080x1920:r=30",
        "-t",
        str(duration_seconds),
        "-vf",
        (
            "drawtext=fontcolor=white:fontsize=56:x=(w-text_w)/2:y=(h-text_h)/2:"
            f"text='{safe_title}'"
        ),
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "FFmpeg render failed")[:1000])
