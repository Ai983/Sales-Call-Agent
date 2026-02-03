from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv


def load_env() -> None:
    load_dotenv()


def import_pipeline() -> Tuple[Optional[object], Optional[str]]:
    try:
        from sales_call_analyzer.pipeline import process_call
    except Exception as exc:  # pragma: no cover - import probe
        return None, str(exc)
    return process_call, None


def check_faster_whisper_import() -> Optional[str]:
    try:
        import faster_whisper  # noqa: F401
    except Exception as exc:
        return str(exc)
    try:
        import av  # noqa: F401
    except Exception as exc:
        return str(exc)
    return None


def check_openai_import() -> Optional[str]:
    try:
        import openai  # noqa: F401
    except Exception as exc:
        return str(exc)
    return None


def env_snapshot(pipeline_error: Optional[str] = None) -> Dict[str, object]:
    ffmpeg_available = shutil.which("ffmpeg") is not None
    ffmpeg_version = ""
    if ffmpeg_available:
        try:
            out = subprocess.run(
                ["ffmpeg", "-version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ).stdout.splitlines()
            ffmpeg_version = out[0] if out else ""
        except Exception:
            ffmpeg_version = ""
    data: Dict[str, object] = {
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "cwd": os.getcwd(),
        "python": sys.executable,
        "venv": os.getenv("VIRTUAL_ENV") or "",
        "ffmpeg_available": ffmpeg_available,
        "ffmpeg_version": ffmpeg_version,
        "import_errors": {},
    }
    if pipeline_error:
        data["import_errors"]["pipeline"] = pipeline_error
    return data
