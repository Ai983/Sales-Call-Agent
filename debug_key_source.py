import os
import pathlib
import re

def mask(k: str) -> str:
    if not k:
        return "None"
    k = k.strip("\n")
    return f"{k[:10]}...{k[-6:]} (len={len(k)})"

def show_repr_tail(k: str) -> str:
    # Helps spot invisible characters
    return repr(k[-12:]) if k else "None"

repo = pathlib.Path(__file__).resolve().parent

# Candidate dotenv locations (common)
candidates = [
    repo / ".env",
    repo / ".env.local",
    repo / "web_api" / ".env",
    repo / "web_api" / ".env.local",
    repo / ".env.example",
]

print("=== CURRENT PROCESS ENV ===")
env_key = os.getenv("OPENAI_API_KEY")
print("OPENAI_API_KEY:", mask(env_key))
print("Tail repr:", show_repr_tail(env_key))

print("\n=== FILE SCAN (KEYS FOUND) ===")
key_line_re = re.compile(r"^\s*OPENAI_API_KEY\s*=\s*(.+?)\s*$")

for p in candidates:
    if not p.exists():
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        print(f"{p}: READ ERROR: {e}")
        continue

    found = []
    for line in text:
        m = key_line_re.match(line)
        if m:
            raw = m.group(1)
            # Strip optional quotes
            raw2 = raw.strip().strip('"').strip("'")
            found.append(raw2)

    if found:
        print(f"\n{p}:")
        for i, k in enumerate(found, 1):
            print(f"  [{i}] {mask(k)}  tail_repr={show_repr_tail(k)}")

print("\n=== SHELL CHECK HINT ===")
print("If env != file, your shell exported a different key than the file contains.")
print("Use: `unset OPENAI_API_KEY` then restart terminal, then set it once via .env OR export (not both).")
