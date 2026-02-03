import os
from pathlib import Path

from web_api.audio_utils import normalize_to_wav


class OpenAITranscriptionError(RuntimeError):
    def __init__(self, class_name, status_code, error_code, error_message):
        self.class_name = class_name
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        status_part = str(status_code) if status_code is not None else "unknown"
        code_part = error_code or "unknown"
        message = error_message or "OpenAI transcription failed."
        super().__init__(f"OpenAI error {status_part} {code_part}: {message}")

def _try_faster_whisper(path):
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None
    try:
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        segments, info = model.transcribe(path, vad_filter=True)
        out = []
        for seg in segments:
            out.append({"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()})
        return out, info.language
    except Exception:
        return None

def _try_openai_whisper(path, raise_on_error=False):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI()
        in_path = Path(path)
        if in_path.suffix.lower() != ".wav":
            normalized = in_path.with_suffix(".normalized.wav")
            normalize_to_wav(in_path, normalized)
            in_path = normalized
        with open(in_path, "rb") as f:
            resp = client.audio.transcriptions.create(model="whisper-1", file=f)
        text = resp.text.strip()
        return [{"start": 0.0, "end": 0.0, "text": text}], None
    except Exception as exc:
        if not raise_on_error:
            return None
        class_name = exc.__class__.__name__
        status_code = getattr(exc, "status_code", None)
        error_code = getattr(exc, "code", None)
        error_message = getattr(exc, "message", None)
        if error_message is None:
            error_message = str(exc)
        raise OpenAITranscriptionError(
            class_name=class_name,
            status_code=status_code,
            error_code=error_code,
            error_message=error_message,
        )

def transcribe_audio(path, backend="faster"):
    if backend == "openai":
        res = _try_openai_whisper(path, raise_on_error=True)
        if res:
            return res
    else:
        res = _try_faster_whisper(path)
        if res:
            return res
        res = _try_openai_whisper(path)
        if res:
            return res
    raise RuntimeError("Transcription unavailable. Install faster-whisper or set OPENAI_API_KEY.")
