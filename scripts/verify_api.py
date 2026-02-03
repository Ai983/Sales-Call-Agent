#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _print(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def _http_get(url, timeout=10):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), resp.read()


def _http_post_multipart(url, fields, file_field, timeout=30):
    boundary = "----verifyapi" + str(int(time.time() * 1000))
    lines = []
    for name, value in fields.items():
        lines.append(f"--{boundary}")
        lines.append(f'Content-Disposition: form-data; name="{name}"')
        lines.append("")
        lines.append(str(value))

    filename, data, content_type = file_field
    lines.append(f"--{boundary}")
    lines.append(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'
    )
    lines.append(f"Content-Type: {content_type}")
    lines.append("")

    body = "\r\n".join(lines).encode("utf-8") + b"\r\n" + data + b"\r\n" + f"--{boundary}--\r\n".encode("utf-8")
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), resp.read()


def _suggest_remediation(error_text):
    text = (error_text or "").lower()
    suggestions = []
    if "openai_api_key" in text:
        suggestions.append("Set OPENAI_API_KEY in your shell or .env file and restart the server.")
    if "openai import failed" in text:
        suggestions.append("Install openai in the active environment (pip install openai).")
    if "invalid api key" in text or "authentication" in text:
        suggestions.append("Check that OPENAI_API_KEY is valid and has access to the API.")
    if "insufficient_quota" in text or "billing" in text:
        suggestions.append("Enable billing / add credits / use a key from a funded project.")
    if "reportlab" in text:
        suggestions.append("Install reportlab (pip install reportlab) in the active environment.")
    if "faster-whisper" in text or "faster_whisper" in text or "av" in text:
        suggestions.append("Install faster-whisper and PyAV with a compatible FFmpeg build for your OS.")
    if "transcription unavailable" in text:
        suggestions.append("Install faster-whisper or set OPENAI_API_KEY for the openai backend.")
    if "openai transcription failed" in text:
        suggestions.append("Verify OPENAI_API_KEY is valid and network access is available.")
    if "no module named" in text:
        suggestions.append("Install missing Python modules and restart the server.")
    if "pipeline import failed" in text:
        suggestions.append("Fix pipeline import errors (reportlab, pydub, faster-whisper) then restart.")
    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Verify Sales Call Analyzer API")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--backend", default="faster", choices=["faster", "openai"])
    args = parser.parse_args()
    failed = False
    skipped = False

    _print("[1/6] Import check")
    try:
        import web_api.main  # noqa: F401
        if not hasattr(web_api.main, "app"):
            raise RuntimeError("web_api.main.app not found")
        _print("- ok: app importable")
    except Exception as exc:
        _print(f"- error: cannot import app: {exc}")
        _print("RESULT: FAIL")
        return 1

    _print("[2/6] Environment")
    _print(f"- OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")

    _print("[3/6] /health")
    try:
        code, body = _http_get(args.base_url + "/health")
        _print(f"- status: {code}")
        _print(f"- body: {body.decode('utf-8')}")
    except Exception as exc:
        _print(f"- error: {exc}")
        _print("RESULT: FAIL")
        return 1

    preferred = os.path.join("inputs", "1st_call_recording.aac")
    if not os.path.exists(preferred):
        _print("[4/6] Upload")
        _print(f"- skip: {preferred} not found")
        skipped = True
        _print("RESULT: SKIP")
        return 2

    _print("[4/6] Upload")
    with open(preferred, "rb") as f:
        data = f.read()
    if not data:
        _print("- error: input file is empty")
        _print("RESULT: FAIL")
        return 1

    ctype = mimetypes.guess_type(preferred)[0] or "application/octet-stream"
    try:
        code, body = _http_post_multipart(
            args.base_url + "/analyze",
            {"backend": args.backend},
            (os.path.basename(preferred), data, ctype),
        )
        _print(f"- status: {code}")
        _print(f"- body: {body.decode('utf-8')}")
        resp = json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8")
        _print(f"- error: HTTP {exc.code}: {err_body}")
        suggestions = _suggest_remediation(err_body)
        if suggestions:
            _print("- remediation:")
            for s in suggestions:
                _print(f"  - {s}")
        _print("RESULT: FAIL")
        return 1
    except Exception as exc:
        _print(f"- error: {exc}")
        _print("RESULT: FAIL")
        return 1

    job_id = resp.get("job_id")
    if not job_id:
        _print("- error: missing job_id in response")
        _print("RESULT: FAIL")
        return 1

    _print("[5/6] Poll job status")
    deadline = time.time() + 180
    status = None
    job = None
    while time.time() < deadline:
        try:
            code, body = _http_get(args.base_url + f"/jobs/{job_id}")
            job = json.loads(body.decode("utf-8"))
            status = job.get("status")
            _print(f"- status: {status}")
            if status in ("done", "error"):
                break
        except Exception as exc:
            _print(f"- error polling: {exc}")
        time.sleep(2)

    if status != "done":
        err_text = (job or {}).get("error") or "timeout or error"
        _print(f"- error: job not done: {err_text}")
        suggestions = _suggest_remediation(err_text)
        if suggestions:
            _print("- remediation:")
            for s in suggestions:
                _print(f"  - {s}")
        _print("RESULT: FAIL")
        return 1

    _print("[6/6] Download outputs")
    out_dir = tempfile.mkdtemp(prefix="verify_api_")
    for name in ("report.pdf", "report.json"):
        url = args.base_url + f"/download/{job_id}/{name}"
        try:
            code, body = _http_get(url, timeout=30)
            path = os.path.join(out_dir, name)
            with open(path, "wb") as f:
                f.write(body)
            size = os.path.getsize(path)
            _print(f"- {name}: {size} bytes (status {code})")
            if size <= 0:
                _print(f"- error: {name} is empty")
                _print("RESULT: FAIL")
                return 1
        except Exception as exc:
            _print(f"- error downloading {name}: {exc}")
            _print("RESULT: FAIL")
            return 1

    _print(f"- success: outputs saved under {out_dir}")
    _print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
