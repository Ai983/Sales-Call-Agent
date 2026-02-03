# UI + API

## One Environment Only

Use a single virtual environment in `.venv` for all API work. Avoid mixing system Python or conda.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-api.txt
```

## Backend (Part 1)

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements-api.txt
```

Run the server:

```bash
uvicorn web_api.main:app --reload --port 8000
```

Test health:

```bash
curl http://localhost:8000/health
```

## Verification

Run the API verifier (server must be running on port 8000):

```bash
python scripts/verify_api.py --backend openai
python scripts/verify_api.py --backend faster
```

## Requirements Split

- `requirements-api.txt`: FastAPI + uvicorn + multipart + dotenv
- `requirements-openai.txt`: OpenAI backend deps (openai + reportlab + pydub)
- `requirements-faster.txt`: Faster-whisper backend deps (faster-whisper + reportlab + pydub)

Install backend deps as needed:

```bash
pip install -r requirements-openai.txt
# or
pip install -r requirements-faster.txt
```

Error meaning (common):
- `OPENAI_API_KEY is not set` → set `OPENAI_API_KEY` in your shell or `.env`, then restart the server.
- `faster-whisper import failed` / `av` errors → install faster-whisper + PyAV with compatible FFmpeg.
- `No module named reportlab` → install reportlab in the active environment.
- `Pipeline import failed` → fix missing analyzer deps (reportlab, pydub, faster-whisper).
