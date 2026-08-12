"""Simple, transparent identifier-column suggestions based on column names.

Detection looks only at column names, never at cell values, and never
modifies any column itself — it only produces suggestions for the user.
"""
import re

_MULTI_WORD_KEYWORDS = [
    "student name", "student id", "child name", "child id",
    "learner name", "learner id", "parent name", "parent phone",
    "parent email", "guardian name", "registration number",
    "admission number", "roll number", "date of birth",
]

_SINGLE_WORD_KEYWORDS = {
    "name", "id", "phone", "mobile", "email", "address", "dob", "guardian",
}


def _normalise(column_name) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(column_name).lower()).strip()


def suggest_identifier_columns(columns) -> list:
    """Return the subset of columns whose names match common identifier patterns."""
    suggestions = []
    for column in columns:
        normalised = _normalise(column)
        tokens = set(normalised.split())

        if any(keyword in normalised for keyword in _MULTI_WORD_KEYWORDS):
            suggestions.append(column)
            continue
        if tokens & _SINGLE_WORD_KEYWORDS:
            suggestions.append(column)

    return suggestions
