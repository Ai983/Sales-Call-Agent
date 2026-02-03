from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from web_api import diagnostics

diagnostics.load_env()


app = FastAPI(title="Sales Call Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

process_call, _PIPELINE_IMPORT_ERROR = diagnostics.import_pipeline()
try:
    from sales_call_analyzer.transcribe import OpenAITranscriptionError
except Exception:
    OpenAITranscriptionError = None

_ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac"}
_ALLOWED_BACKENDS = {"faster", "openai"}
_JOB_STORE = {}
_JOB_LOCK = Lock()
_EXECUTOR = ThreadPoolExecutor(max_workers=2)
_LOG = logging.getLogger("web_api")
logging.basicConfig(level=logging.INFO)


@app.get("/health")
def health():
    if _PIPELINE_IMPORT_ERROR:
        return {"ok": False, "error": _PIPELINE_IMPORT_ERROR}
    return {"ok": True}


@app.get("/env")
def env():
    return diagnostics.env_snapshot(pipeline_error=_PIPELINE_IMPORT_ERROR)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _set_job(job_id, **updates):
    with _JOB_LOCK:
        job = _JOB_STORE.get(job_id)
        if not job:
            return
        job.update(updates)
        job["updated_at"] = _now_iso()


def _run_analysis(job_id, upload_path, backend, filename):
    _set_job(job_id, status="running")
    _LOG.info("job_start job_id=%s backend=%s filename=%s", job_id, backend, filename)
    try:
        if _PIPELINE_IMPORT_ERROR:
            raise RuntimeError(_PIPELINE_IMPORT_ERROR)
        out_root = os.path.join("outputs", "web", job_id)
        os.makedirs(out_root, exist_ok=True)
        metrics, pdf_path = process_call(upload_path, out_root, backend=backend)
        json_path = metrics.get("output_json_path") if isinstance(metrics, dict) else None
        if not (os.path.exists(pdf_path) and os.path.exists(json_path)):
            raise RuntimeError("Expected output files not found.")
        _set_job(
            job_id,
            status="done",
            output_dir=str(Path(pdf_path).parent),
            pdf_path=pdf_path,
            json_path=json_path,
            error=None,
        )
        _LOG.info("job_done job_id=%s backend=%s filename=%s", job_id, backend, filename)
    except Exception as exc:
        err_msg = str(exc)
        openai_error = None
        if OpenAITranscriptionError and isinstance(exc, OpenAITranscriptionError):
            openai_error = {
                "class_name": exc.class_name,
                "status_code": exc.status_code,
                "code": exc.error_code,
                "message": exc.error_message,
            }
        if backend == "openai" and "Transcription unavailable" in err_msg:
            err_msg = (
                "OpenAI transcription failed (check OPENAI_API_KEY/network). "
                "Fallback to faster-whisper was unavailable."
            )
        _set_job(job_id, status="error", error=err_msg, openai_error=openai_error)
        _LOG.error("job_error job_id=%s backend=%s filename=%s error=%s", job_id, backend, filename, err_msg)


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    backend: str = Form("faster"),
):
    if backend not in _ALLOWED_BACKENDS:
        raise HTTPException(status_code=400, detail="Invalid backend. Use 'faster' or 'openai'.")
    original_name = os.path.basename(file.filename or "")
    if not original_name:
        raise HTTPException(status_code=400, detail="Filename is required.")
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    job_id = str(uuid4())
    upload_dir = os.path.join("uploads", job_id)
    os.makedirs(upload_dir, exist_ok=True)
    upload_path = os.path.join(upload_dir, original_name)
    with open(upload_path, "wb") as f:
        f.write(content)

    created_at = _now_iso()
    with _JOB_LOCK:
        _JOB_STORE[job_id] = {
            "job_id": job_id,
            "status": "uploaded",
            "filename": original_name,
            "backend": backend,
            "created_at": created_at,
            "updated_at": created_at,
            "output_dir": None,
            "pdf_path": None,
            "json_path": None,
            "openai_error": None,
            "error": None,
        }

    if _PIPELINE_IMPORT_ERROR:
        _set_job(job_id, status="error", error=f"Pipeline import failed: {_PIPELINE_IMPORT_ERROR}")
        raise HTTPException(
            status_code=400,
            detail={"message": f"Pipeline import failed: {_PIPELINE_IMPORT_ERROR}", "job_id": job_id},
        )

    if backend == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            _set_job(job_id, status="error", error="OPENAI_API_KEY is not set.")
            raise HTTPException(
                status_code=400,
                detail={"message": "OPENAI_API_KEY is not set.", "job_id": job_id},
            )
        openai_error = diagnostics.check_openai_import()
        if openai_error:
            _set_job(job_id, status="error", error=f"openai import failed: {openai_error}")
            raise HTTPException(
                status_code=400,
                detail={"message": f"openai import failed: {openai_error}", "job_id": job_id},
            )
    if backend == "faster":
        faster_error = diagnostics.check_faster_whisper_import()
        if faster_error:
            _set_job(job_id, status="error", error=f"faster-whisper import failed: {faster_error}")
            raise HTTPException(
                status_code=400,
                detail={"message": f"faster-whisper import failed: {faster_error}", "job_id": job_id},
            )

    _EXECUTOR.submit(_run_analysis, job_id, upload_path, backend, original_name)

    return {
        "job_id": job_id,
        "status": "uploaded",
        "filename": original_name,
        "backend": backend,
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with _JOB_LOCK:
        job = _JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/download/{job_id}/report.pdf")
def download_pdf(job_id: str):
    with _JOB_LOCK:
        job = _JOB_STORE.get(job_id)
    if not job or job.get("status") != "done":
        raise HTTPException(status_code=404, detail="Report not available.")
    pdf_path = job.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(pdf_path, media_type="application/pdf", filename="report.pdf")


@app.get("/download/{job_id}/report.json")
def download_json(job_id: str):
    with _JOB_LOCK:
        job = _JOB_STORE.get(job_id)
    if not job or job.get("status") != "done":
        raise HTTPException(status_code=404, detail="Report not available.")
    json_path = job.get("json_path")
    if not json_path or not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(json_path, media_type="application/json", filename="report.json")
