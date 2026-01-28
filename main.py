import argparse
import os
import json
from pathlib import Path
from sales_call_analyzer.pipeline import process_call

def main():
    parser = argparse.ArgumentParser(description="Sales Call Analyzer")
    parser.add_argument("inputs", nargs="+", help="Input MP3 files")
    parser.add_argument("--out", default="outputs", help="Output directory")
    parser.add_argument("--backend", default="faster", choices=["faster","openai"], help="Transcription backend")
    args = parser.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    results = []
    for input_path in args.inputs:
        call_json, pdf_path = process_call(input_path, out_root, backend=args.backend)
        results.append({"input": input_path, "json": call_json["output_json_path"], "pdf": str(pdf_path)})

    print(json.dumps({"results": results}, ensure_ascii=False))

if __name__ == "__main__":
    main()
