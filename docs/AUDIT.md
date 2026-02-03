# Audit Report

Date: February 3, 2026

## Scope
This report covers all changes made by Codex in this repo and the current environment observations.

## Modified / Added Files

- `web_api/main.py`
  - Added diagnostics integration, `/env` endpoint, backend validation, thread-safe job store updates, background execution, and download endpoints.
  - Added dependency checks for `openai`, `faster-whisper`, and `av` to fail early with clear errors.
  - Added structured logging for job lifecycle events.

- `web_api/diagnostics.py`
  - New module for dotenv loading, pipeline import probing, backend import checks, and environment snapshot reporting.

- `web_api/requirements.txt`
  - Added `python-dotenv` for consistent `.env` loading.

- `README_UI.md`
  - Added “One Environment Only” section for `.venv` usage.
  - Updated dependency install commands to use `requirements-api.txt`.
  - Added verification and requirements split guidance.

- `scripts/verify_api.py`
  - Added deterministic PASS/FAIL/SKIP output.
  - Added clearer remediation hints and structured validation steps.
  - Prepends repo root to `sys.path` for stable import checks.

- `requirements-api.txt`
  - New: FastAPI, uvicorn, multipart, dotenv.

- `requirements-openai.txt`
  - New: OpenAI backend deps (openai + reportlab + pydub).

- `requirements-faster.txt`
  - New: Faster backend deps (faster-whisper + reportlab + pydub).

- `Makefile`
  - New: `make venv`, `make install-api`, `make run-api`, `make verify-openai`, `make verify-faster` targets.

- `docs/ENV_DEBUG.md`
  - New: Captures the active Python, pip, uvicorn paths, and import sanity.

- `docs/AUDIT.md`
  - New: this report.

- `inputs/1st_call_recording.aac`
  - Renamed from `inputs/1st call recording .aac` (in git status).

- `inputs/2nd_recording.aac`
  - Added (in git status).

- `uploads/`
  - Runtime artifacts created by `/analyze` uploads (untracked).

- `.venv/`
  - Local Python virtual environment created for deterministic runs (untracked).

## Key Behavior Changes (Summary)

- API now loads `.env` at startup and exposes `/env` to confirm environment visibility without leaking secrets.
- Backend selection is explicit: only `openai` or `faster`.
- OpenAI backend requires both `OPENAI_API_KEY` and the `openai` module; failures are detected before job execution.
- Faster backend is treated as optional: if `faster-whisper` or `av` import fails, the API returns a clear 400 error and does not attempt analysis.
- Verification script provides deterministic PASS/FAIL output and remediation hints.

## Environment Findings

See `docs/ENV_DEBUG.md` for the current shell environment snapshot. It shows mixed Python paths (system Python vs conda), which motivated the “One Environment Only” guidance.

## Commands to Reproduce Current Behavior (End-to-End)

From repo root:

```bash
# Create and activate a single venv
python -m venv .venv
source .venv/bin/activate

# Install API + OpenAI backend deps
python -m pip install -r requirements-api.txt -r requirements-openai.txt

# Start API
python -m uvicorn web_api.main:app --reload --port 8000

# In another terminal (same .venv)
python scripts/verify_api.py --backend openai
```

Alternate via Makefile:

```bash
make venv
make install-api
make run-api
# new terminal
make verify-openai
```

## Verification Results (OpenAI Backend)

Latest run failed with:

- `OpenAI transcription failed (check OPENAI_API_KEY/network). Fallback to faster-whisper was unavailable.`

This indicates the OpenAI transcription call failed and the fallback to `faster-whisper` was unavailable. Possible causes:
- `OPENAI_API_KEY` is invalid or has no access.
- Network access blocked.
- OpenAI API error.

## Known Constraints / Outstanding Items

- Faster backend remains optional on macOS due to PyAV/FFmpeg build issues; API will return a clear error if dependencies are missing.
- OpenAI backend requires a valid key and network access; without those, the verifier fails as above.
