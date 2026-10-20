"""Reusable data loading, cleaning, and CRM module analysis helpers."""

from pathlib import Path

import pandas as pd


MODULE_COLUMNS = {
    "leads": "Status",
    "contacts": "Company",
    "accounts": "Industry",
    "deals": "Stage",
    "products": "Category",
    "campaigns": "Status",
    "tickets": "Status",
    "quotes": "Status",
    "tasks": "Status",
    "activities": "Type",
    "notifications": "Type",
}


def load_data(file_name, sheet_name=0):
    path = Path(file_name)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet_name)
    raise ValueError(f"Unsupported dataset format: {path.suffix or '(no extension)'}")


def _find_column(df, requested):
    if not requested:
        return None
    return next((column for column in df.columns if str(column).strip().casefold() == requested.casefold()), None)


def _category_chart(df, column):
    """Return CRM-renderable chart data; the CRM UI renders this JSON as a bar chart."""
    counts = df[column].fillna("Missing").astype(str).value_counts(dropna=False)
    return {
        "title": f"Record count by {column}",
        "type": "bar",
        "labels": [str(label) for label in counts.index],
        "values": [int(value) for value in counts.values],
    }


def analyze_module(df, module="dataset"):
    module_key = str(module or "dataset").strip().casefold()
    requested_column = MODULE_COLUMNS.get(module_key)
    column = _find_column(df, requested_column)
    if column is None:
        # For unfamiliar schemas, choose the first categorical column with useful values.
        candidates = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        column = next((c for c in candidates if 1 < df[c].nunique(dropna=True) <= 30), None)

    summary = [
        {"label": "Input rows", "value": int(len(df))},
        {"label": "Missing values", "value": int(df.isna().sum().sum())},
        {"label": "Duplicate rows", "value": int(df.duplicated().sum())},
        {"label": "Total columns", "value": int(len(df.columns))},
    ]
    charts = []
    if column is not None:
        summary.append({"label": f"{column} categories", "value": int(df[column].nunique(dropna=True))})
        charts.append(_category_chart(df, column))
    return {
        "title": f"{module_key.title()} dataset analysis",
        "summary": summary,
        "charts": charts,
        "logs": [f"Analyzed {len(df)} rows across {len(df.columns)} columns."],
    }


def raw_dataset_report(df, column=None, dataset_name=""):
    """Backward-compatible entry point for a general or selected-column report."""
    report = analyze_module(df, dataset_name or "dataset")
    selected = _find_column(df, column)
    if selected is not None:
        report["charts"] = [_category_chart(df, selected)]
        report["summary"].append({"label": f"{selected} categories", "value": int(df[selected].nunique(dropna=True))})
    report["title"] = f"Analysis of {dataset_name}" if dataset_name else report["title"]
    report["duplicates"] = int(df.duplicated().sum())
    return report


def clean_data(df, drop_missing_record_from_column=None, remove_duplicated=True):
    cleaned = df.copy()
    original_rows = len(cleaned)
    if drop_missing_record_from_column:
        requested = drop_missing_record_from_column
        if isinstance(requested, str):
            requested = [requested]
        available = [column for column in requested if column in cleaned.columns]
        if available:
            cleaned = cleaned.dropna(subset=available)
    if remove_duplicated:
        cleaned = cleaned.drop_duplicates()
    cleaned = cleaned.reset_index(drop=True)
    return {
        "title": "Data cleaning",
        "summary": [
            {"label": "Original rows", "value": int(original_rows)},
            {"label": "Final rows", "value": int(len(cleaned))},
            {"label": "Removed rows", "value": int(original_rows - len(cleaned))},
        ],
        "data": cleaned,
    }
