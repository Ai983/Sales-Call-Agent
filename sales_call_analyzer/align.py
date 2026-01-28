def align_transcript_to_speakers(transcript_segments, speaker_segments):
    if not transcript_segments:
        return []
    if not speaker_segments:
        return [{"start": s.get("start", 0.0), "end": s.get("end", 0.0), "speaker": "SPEAKER_0", "text": s["text"]} for s in transcript_segments]
    out = []
    si = 0
    for t in transcript_segments:
        ts = t.get("start", 0.0)
        while si + 1 < len(speaker_segments) and speaker_segments[si]["end"] < ts:
            si += 1
        spk = speaker_segments[min(si, len(speaker_segments) - 1)]["speaker"]
        out.append({"start": t.get("start", 0.0), "end": t.get("end", 0.0), "speaker": spk, "text": t["text"]})
    return out

