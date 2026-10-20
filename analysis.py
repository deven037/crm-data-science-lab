"""Analyze one CRM dataset and print one JSON report for the CRM bridge."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from methods.methods import analyze_module, clean_data, load_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--module", default=None, help="CRM module (leads, contacts, deals, etc.)")
    args = parser.parse_args()

    df = load_data(args.dataset)
    module = args.module or args.dataset.stem.split("-")[0]
    report = analyze_module(df, module)

    cleaned = clean_data(df)
    df = cleaned["data"]
    report["summary"].extend(cleaned["summary"])

    processed_dir = args.output_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", args.dataset.stem).strip("-") or "dataset"
    processed_path = processed_dir / f"{safe_name}-cleaned.csv"
    df.to_csv(processed_path, index=False, encoding="utf-8-sig")
    report["processed_dataset"] = processed_path.relative_to(args.output_dir).as_posix()
    report["logs"].append(f"Saved cleaned dataset to {processed_path.name}.")

    # The CRM UI receives chart labels and values in the JSON report. A local PNG
    # alone would not be available to the hosted CRM bridge.
    print(json.dumps(report, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
