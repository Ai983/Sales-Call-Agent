Sales Call Analyzer — Interior Build & Design

Overview
This tool analyzes one or more MP3 sales calls and generates for each call:
- A structured JSON containing transcript-derived metrics
- A professional PDF report with clear sections and an embedded JSON appendix

Key Features
- Transcription with Whisper (local) or OpenAI Whisper API when configured
- Naive diarization fallback, with role assignment via keyword heuristics
- Engagement metrics, keyword counts, numeric mentions, language percentages
- Sentiment scoring using transformers or rule-based fallback
- PDF generation using ReportLab

Quick Start
1. Place audio files (mp3/aac/wav) under `inputs/`
2. Run: `python main.py inputs/* --backend faster`
3. Optional: force OpenAI Whisper with `--backend openai` (requires `OPENAI_API_KEY`)
4. Outputs appear under `outputs/<base>_<timestamp>/report.json` and `outputs/<base>_<timestamp>/report.pdf`

Environment
- Optional: `OPENAI_API_KEY` to enable OpenAI Whisper transcription or LLM insights
