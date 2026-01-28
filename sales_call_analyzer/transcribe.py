import os
from pathlib import Path

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

def _try_openai_whisper(path):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI()
        with open(path, "rb") as f:
            resp = client.audio.transcriptions.create(model="whisper-1", file=f)
        text = resp.text.strip()
        return [{"start": 0.0, "end": 0.0, "text": text}], None
    except Exception:
        return None

def transcribe_audio(path, backend="faster"):
    if backend == "openai":
        res = _try_openai_whisper(path)
        if res:
            return res
        res = _try_faster_whisper(path)
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
