def diarize_audio(path):
    from pydub import AudioSegment, silence
    audio = AudioSegment.from_file(path)
    chunks = silence.detect_nonsilent(audio, min_silence_len=600, silence_thresh=audio.dBFS - 16)
    segments = []
    speaker = 0
    for start_ms, end_ms in chunks:
        segments.append({"start": start_ms / 1000.0, "end": end_ms / 1000.0, "speaker": f"SPEAKER_{speaker}"})
        speaker = 1 - speaker
    if not segments:
        segments.append({"start": 0.0, "end": len(audio) / 1000.0, "speaker": "SPEAKER_0"})
    return segments
