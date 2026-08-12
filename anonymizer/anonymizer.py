"""Core de-identification logic.

Every function here operates on in-memory pandas objects only. No cell
values are logged, and no mapping is retained after the function that
built it returns.
"""
from __future__ import annotations

import pandas as pd

ID_PREFIX = "ANON_"
ID_WIDTH = 5


def _is_missing(value) -> bool:
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def pseudonymise_column(series: pd.Series) -> tuple[pd.Series, dict]:
    """Replace values in a single column with sequential anonymous IDs.

    Repeated values receive the same ID. Missing/blank values are left
    unchanged. The returned mapping is local to this single column and is
    never combined with any other column's mapping.
    """
    mapping: dict = {}
    counter = 1
    result = []
    for value in series:
        if _is_missing(value):
            result.append(value)
            continue
        if value not in mapping:
            mapping[value] = f"{ID_PREFIX}{counter:0{ID_WIDTH}d}"
            counter += 1
        result.append(mapping[value])
    return pd.Series(result, index=series.index), mapping


def process_dataframe(df: pd.DataFrame, column_actions: dict) -> tuple[pd.DataFrame, dict]:
    """Apply per-column Delete/Pseudonymise actions independently.

    column_actions maps column name -> "delete" | "pseudonymise". Columns
    not present in column_actions are preserved unchanged. Rows are never
    combined, reordered, or reshaped.
    """
    result = df.copy()
    summary = {
        "rows": len(df),
        "original_columns": len(df.columns),
        "columns_deleted": [],
        "columns_pseudonymised": [],
        "unique_values_pseudonymised": {},
    }

    for column, action in column_actions.items():
        if column not in df.columns:
            continue
        if action == "delete":
            result = result.drop(columns=[column])
            summary["columns_deleted"].append(column)
        elif action == "pseudonymise":
            pseudonymised_series, mapping = pseudonymise_column(df[column])
            result[column] = pseudonymised_series
            summary["columns_pseudonymised"].append(column)
            summary["unique_values_pseudonymised"][column] = len(mapping)

    return result, summary
