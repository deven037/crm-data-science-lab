"""Starter analysis contract for Practice CRM Data Studio.

Edit this file in PyCharm. Print exactly one JSON object to stdout containing
summary, charts, and logs. Optional image files saved beneath output-dir are
automatically listed in the CRM analysis results.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    with args.dataset.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        columns = list(reader.fieldnames or [])
        raw_rows = list(reader)

    trimmed_rows = [
        {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
        for row in raw_rows
    ]
    nonblank_rows = [row for row in trimmed_rows if any((value or "") != "" for value in row.values())]
    unique_rows = []
    seen = set()
    for row in nonblank_rows:
        row_key = tuple(row.get(column, "") or "" for column in columns)
        if row_key in seen:
            continue
        seen.add(row_key)
        unique_rows.append(row)
    rows = unique_rows

    args.output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = args.output_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    base_name = re.sub(r"-cleaned$", "", re.sub(r"-\d{8}-\d{6}(?:-\d{6})?$", "", args.dataset.stem), flags=re.IGNORECASE)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    processed_path = processed_dir / f"{base_name}-cleaned-{stamp}.csv"
    with processed_path.open("x", newline="", encoding="utf-8-sig") as destination:
        writer = csv.DictWriter(destination, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    status_column = next((column for column in columns if column.strip().casefold() == "status"), None)
    status_counts = Counter((row.get(status_column, "") or "Missing") for row in rows) if status_column else Counter()
    numeric_columns = []
    for column in columns:
        values = []
        for row in rows:
            try:
                values.append(float(row[column]))
            except (TypeError, ValueError):
                continue
        if values:
            numeric_columns.append({"label": column, "mean": round(sum(values) / len(values), 2), "non_missing": len(values)})

    report = {
        "title": f"Analysis of {args.dataset.name}",
        "summary": [
            {"label": "Input rows", "value": len(raw_rows)},
            {"label": "Clean rows", "value": len(rows)},
            {"label": "Blank rows removed", "value": len(raw_rows) - len(nonblank_rows)},
            {"label": "Duplicates removed", "value": len(nonblank_rows) - len(rows)},
            {"label": "Columns", "value": len(columns)},
            {"label": "Status categories", "value": len(status_counts)},
        ],
        "processed_dataset": f"processed/{processed_path.name}",
        "charts": [
            {
                "title": "Record count by status",
                "type": "bar",
                "labels": list(status_counts.keys()),
                "values": list(status_counts.values()),
            }
        ] if status_counts else [],
        "tables": [
            {"title": "Numeric column summary", "columns": ["Column", "Mean", "Non-missing"], "rows": [[item["label"], item["mean"], item["non_missing"]] for item in numeric_columns]}
        ],
        "logs": [f"Loaded {len(raw_rows)} rows from {args.dataset.name}.", "Trimmed text cells, removed fully blank rows, and removed duplicate rows.", f"Saved cleaned data to {processed_path.name}.", "Edit analysis.py to implement your own analysis."],
    }
    print(json.dumps(report, ensure_ascii=True))


if __name__ == "__main__":
    main()
