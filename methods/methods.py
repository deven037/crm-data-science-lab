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


def numeric_statistics_tables(df):
    """Build tables for numeric summaries, position, spread, and outliers.

    Standard deviation and variance use population formulas (ddof=0). Outliers
    are values outside the usual 1.5 * IQR fences.
    """
    central_position_rows = []
    spread_outlier_rows = []
    for column in df.columns:
        if not pd.api.types.is_numeric_dtype(df[column]):
            continue

        values = df[column].dropna()
        if values.empty:
            continue

        q1 = float(values.quantile(0.25))
        median = float(values.quantile(0.50))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        modes = values.mode()
        mode_text = ", ".join(str(round(float(value), 2)) for value in modes)
        outlier_count = int(((values < lower_fence) | (values > upper_fence)).sum())

        central_position_rows.append([
            str(column),
            int(values.count()),
            round(float(values.mean()), 2),
            round(median, 2),
            mode_text,
            round(float(values.quantile(0.10)), 2),
            round(q1, 2),
            round(median, 2),
            round(q3, 2),
            round(float(values.quantile(0.90)), 2),
        ])
        spread_outlier_rows.append([
            str(column),
            round(float(values.min()), 2),
            round(float(values.max()), 2),
            round(float(values.max() - values.min()), 2),
            round(float(values.var(ddof=0)), 2),
            round(float(values.std(ddof=0)), 2),
            round(iqr, 2),
            round(lower_fence, 2),
            round(upper_fence, 2),
            outlier_count,
        ])

    if not central_position_rows:
        return []

    return [
        {
            "title": "Central tendency and position",
            "columns": ["Column", "Count", "Mean", "Median", "Mode", "P10", "Q1 / P25", "Q2 / P50", "Q3 / P75", "P90"],
            "rows": central_position_rows,
        },
        {
            "title": "Spread and outliers",
            "columns": ["Column", "Minimum", "Maximum", "Range", "Variance", "Std dev", "IQR", "Lower fence", "Upper fence", "Outlier count"],
            "rows": spread_outlier_rows,
        },
    ]


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
    for numeric_column in df.columns:
        if pd.api.types.is_numeric_dtype(df[numeric_column]):
            values = df[numeric_column].dropna()
            if not values.empty:
                summary.extend([
                    {"label": f"{numeric_column} total", "value": round(float(values.sum()), 2)},
                    {"label": f"{numeric_column} average", "value": round(float(values.mean()), 2)},
                ])

    tables = []
    charts = []
    if column is not None:
        summary.append({
            "label": f"{column} categories",
            "value": int(df[column].nunique(dropna=True)),
        })
        charts.append(_category_chart(df, column))
        tables.append(category_distribution_table(df, column))

    # When both field types are available, compare the numeric measure across
    # each category (for example, average Value for each Source).
    numeric_columns = [
        c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
    ]
    if column is not None and numeric_columns:
        numeric_column = numeric_columns[0]
        grouped_averages = df.groupby(column, dropna=False)[numeric_column].mean().dropna()
        if not grouped_averages.empty:
            charts.append({
                "title": f"Average {numeric_column} by {column}",
                "type": "bar",
                "labels": ["Missing" if pd.isna(label) else str(label) for label in grouped_averages.index],
                "values": [round(float(value), 2) for value in grouped_averages.values],
            })
    return {
        "title": f"{module_key.title()} dataset analysis",
        "summary": summary,
        "charts": charts,
        "tables": tables,
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

    #standardized columns
    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        cleaned[column] = cleaned[column].str.strip()

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

    validated_rows = []
    value_column = _find_column(cleaned, "Value")

    if value_column is not None:
        numeric_values = pd.to_numeric(cleaned[value_column], errors='coerce')
        negative_count = int((numeric_values < 0).sum())
        validated_rows.append({
            "label" : "Negative Values Rows",
            "value" : negative_count
        })

    return {
        "title": "Data cleaning",
        "summary": [
            {"label": "Original rows", "value": int(original_rows)},
            {"label": "Final rows", "value": int(len(cleaned))},
            {"label": "Removed rows", "value": int(original_rows - len(cleaned))},
        ] + validated_rows,
        "data": cleaned,
    }

def missing_values_table(df):
    rows = []
    logs = []

    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        missing_percentage = (
            round(missing_count / len(df) * 100, 2)
            if len(df) > 0
            else 0
        )

        rows.append([
            str(column),
            missing_count,
            missing_percentage,
        ])

    rows_with_missing = df[df.isna().any(axis=1)]
    log_limit = 20
    for index, record in rows_with_missing.head(log_limit).iterrows():
        missing_columns = record.index[record.isna()].tolist()
        logs.append(
            f"Dataset row {index + 1} has missing values in {missing_columns}: "
            f"{record.to_dict()}"
        )

    remaining = len(rows_with_missing) - min(len(rows_with_missing), log_limit)
    if remaining > 0:
        logs.append(f"{remaining} more rows with missing values were not listed.")

    table = {
        "title": "Missing Value Table",
        "columns": ["Column", "Missing Count", "Missing Percentage"],
        "rows": rows,
    }
    return table, logs

def category_distribution_table(df, column):
    """Return each category's count and percentage of all dataset rows."""
    values = df[column].fillna("Missing").astype(str)
    counts = values.value_counts(dropna=False)
    total_rows = len(values)

    rows = []
    for category, count in counts.items():
        percentage = count / total_rows * 100 if total_rows else 0
        rows.append([
            str(category),
            int(count),
            round(percentage, 2),
        ])

    return {
        "title": f"{column} distribution",
        "columns": ["Category", "Count", "Percentage of rows"],
        "rows": rows,
    }