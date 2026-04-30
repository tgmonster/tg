import asyncio
import os
import shutil
from pathlib import Path

from config import AUDIO_OUTPUT_FORMAT, AUDIO_TARGET_BITRATE, AUDIO_TARGET_CODEC


def _ffmpeg_exists() -> bool:
    return shutil.which("ffmpeg") is not None


def _target_path(source_path: str, ext: str) -> str:
    p = Path(source_path)
    return str(p.with_name(f"{p.stem}.optimized.{ext}"))


async def compress_audio_file(source_path: str) -> tuple[str, bool]:
    """
    Returns (path, changed)
    - path: compressed file path or original
    - changed: True if compressed artifact was generated
    """
    if not source_path or not os.path.exists(source_path):
        return source_path, False
    if not _ffmpeg_exists():
        return source_path, False

    output_path = _target_path(source_path, AUDIO_OUTPUT_FORMAT)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        source_path,
        "-vn",
        "-c:a",
        AUDIO_TARGET_CODEC,
        "-b:a",
        AUDIO_TARGET_BITRATE,
        "-movflags",
        "+faststart",
        output_path,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()
    if proc.returncode != 0 or not os.path.exists(output_path):
        if os.path.exists(output_path):
            os.remove(output_path)
        return source_path, False

    src_size = os.path.getsize(source_path)
    out_size = os.path.getsize(output_path)
    if out_size >= src_size:
        os.remove(output_path)
        return source_path, False
    return output_path, True
