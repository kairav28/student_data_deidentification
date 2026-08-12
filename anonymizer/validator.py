"""Validation errors and checks used across the application.

Error messages are user-facing and must never include dataset values.
"""


class DeidentificationError(Exception):
    """Base class for all user-facing de-identification errors."""


class UnsupportedFileTypeError(DeidentificationError):
    pass


class MultiSheetExcelError(DeidentificationError):
    pass


class EmptyFileError(DeidentificationError):
    pass


class EmptyDatasetError(DeidentificationError):
    pass


class NoColumnsError(DeidentificationError):
    pass


class NoActionsSelectedError(DeidentificationError):
    pass


class FileReadError(DeidentificationError):
    pass


MESSAGES = {
    UnsupportedFileTypeError: "Please upload a CSV or Excel (.xlsx) file.",
    MultiSheetExcelError: (
        "Excel files must contain exactly one worksheet. "
        "Please upload a workbook containing only one worksheet."
    ),
    EmptyFileError: "The uploaded file appears to be empty.",
    EmptyDatasetError: "The dataset does not contain any rows.",
    NoColumnsError: "The dataset does not contain any columns.",
    NoActionsSelectedError: "Please select at least one column to delete or pseudonymise.",
    FileReadError: (
        "There was a problem reading the uploaded file. "
        "Please check that it is a valid CSV or Excel file."
    ),
}


def validate_column_actions(column_actions: dict) -> None:
    """Raise NoActionsSelectedError if no column has an active action."""
    if not any(action in ("delete", "pseudonymise") for action in column_actions.values()):
        raise NoActionsSelectedError(MESSAGES[NoActionsSelectedError])
