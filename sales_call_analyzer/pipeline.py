import os
import json
from pathlib import Path
from sales_call_analyzer.transcribe import transcribe_audio
from sales_call_analyzer.diarize import diarize_audio
from sales_call_analyzer.align import align_transcript_to_speakers
from sales_call_analyzer.analysis import analyze_metrics
from sales_call_analyzer.pdf_generator import generate_pdf
from sales_call_analyzer.utils import timestamp_id, safe_filename

def process_call(input_path, out_root, backend="faster"):
    call_id = timestamp_id()
    base = safe_filename(Path(input_path).stem)
    call_dir = Path(out_root) / f"{base}_{call_id}"
    call_dir.mkdir(parents=True, exist_ok=True)

    transcript_segments, language_hint = transcribe_audio(input_path, backend=backend)
    speaker_segments = diarize_audio(input_path)
    labeled_segments = align_transcript_to_speakers(transcript_segments, speaker_segments)
    metrics = analyze_metrics(labeled_segments, input_path)

    json_path = call_dir / "report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    pdf_path = call_dir / "report.pdf"
    generate_pdf(metrics, pdf_path)

    metrics["output_json_path"] = str(json_path)
    metrics["output_pdf_path"] = str(pdf_path)
    return metrics, pdf_path
