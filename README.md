# Student Data De-identification Tool

A simple, transparent Streamlit application for de-identifying student
datasets. Upload a CSV or single-sheet Excel (`.xlsx`) file, choose which
columns contain identifying information, and either **delete** those
columns or **pseudonymise** them with sequential anonymous IDs
(`ANON_00001`, `ANON_00002`, ...).

> De-identification removes or replaces the identifiers selected by the
> user. It does not guarantee that an individual cannot be re-identified
> using other information in the dataset. Users are responsible for
> reviewing the resulting dataset before sharing it.

## Privacy

This application is designed for sensitive student/child data and does
**not** deliberately persist anything you upload or process:

- Files are read and processed entirely in memory (pandas DataFrames and
  `BytesIO` buffers) — nothing is written to disk.
- No database, upload folder, output folder, or identifier-mapping file is
  created.
- No data is sent to any external API or LLM.
- No cell values or personally identifying information are logged.
- Nothing is retained between sessions or between uploads — every upload is
  processed completely independently.

This does not guarantee that data cannot exist temporarily in the
underlying hosting infrastructure (e.g. OS-level memory paging). The
application itself simply never deliberately persists it.

## Features

- Accepts `.csv` and single-sheet `.xlsx` files; multi-sheet workbooks are
  rejected with a clear error.
- Shows a preview of the dataset (file name, row/column counts, column
  names, first 10 rows) before you make any decisions.
- Explains the difference between long-format and wide/short-format data
  with examples (informational only — it does not affect processing).
- Suggests likely identifier columns based on column name (e.g. "Student
  Name", "Parent Phone", "Email") — suggestions never auto-apply an action.
- Lets you choose, independently for every column: **Keep**, **Delete**, or
  **Pseudonymise**.
- Every pseudonymised column is mapped completely independently of every
  other column — columns and rows are never combined to determine identity.
- Repeated values within a column always get the same anonymous ID; missing
  or blank values are always left as missing.
- Shows a final review of exactly what will change before you click
  **De-identify Dataset**.
- After processing, shows a summary (rows processed, columns deleted,
  columns pseudonymised, unique values pseudonymised per column) and an
  explicit **Download De-identified Dataset** button. Nothing downloads
  automatically.
- Output file format always matches the input file format (CSV → CSV,
  `.xlsx` → `.xlsx`).

## Requirements

- Python 3.10+

## Installation and running

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) — open
it in your browser to use the application. No other software installation
is required to use the app once it is running.

## Running the tests

```bash
pip install -r requirements.txt
pytest
```

## Project structure

```text
student-data-deidentifier/
│
├── CLAUDE.md
├── app.py                     # Streamlit UI (7-step workflow)
├── requirements.txt
├── README.md
│
├── anonymizer/
│   ├── __init__.py
│   ├── file_handler.py        # In-memory CSV/Excel reading and writing
│   ├── detector.py            # Column-name based identifier suggestions
│   ├── anonymizer.py          # Core de-identification logic
│   └── validator.py           # Error types and validation checks
│
└── tests/
    ├── test_file_handler.py
    ├── test_anonymizer.py
    └── test_validator.py
```

The core de-identification logic (`anonymizer/`) has no dependency on
Streamlit and is fully testable on its own, as demonstrated by the test
suite.

## How column actions work

Each selected column is processed **completely independently**:

```text
Student Name:
Rahul → ANON_00001
Aisha → ANON_00002

Student ID:
123 → ANON_00001
456 → ANON_00002
```

These are two separate mappings built independently from each column's own
values. The application never combines columns (e.g. Student Name +
Student ID) or rows to determine identity, and never creates composite
identifiers. Sequential IDs are pseudonymous identifiers, not a guarantee
of complete anonymity.

## Limitations

- Sequential pseudonymous IDs do not, on their own, guarantee that an
  individual cannot be re-identified from the rest of the dataset (e.g. via
  rare combinations of school, grade, and score). Users should review the
  output before sharing it.
- Only `.csv` and single-sheet `.xlsx` files are supported. `.xls`, `.xlsm`,
  `.xlsb`, and multi-sheet workbooks are rejected by design.
- The long/wide-format selection is informational only and does not change
  how the dataset is processed.
- Because every upload is processed independently and no mapping is
  retained, the same student appearing in two different uploaded files will
  not necessarily receive the same anonymous ID across those files. This is
  intentional.
