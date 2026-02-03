from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def normalize_to_wav(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("Audio conversion failed: ffmpeg not found. Install ffmpeg (brew install ffmpeg).")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Audio conversion failed: ffmpeg error.") from exc

    if not output_path.exists() or output_path.stat().st_size <= 0:
        raise RuntimeError("Audio conversion failed: output file missing or empty.")

    return output_path
