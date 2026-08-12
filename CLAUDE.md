# Student Data De-identification Tool

## 1. Project purpose

Build a small, reliable web application using **Python + Streamlit** that allows a user to upload a student dataset, select columns containing identifying information, and either:

1. Delete those columns, or
2. Pseudonymise the values in those columns using sequential anonymous IDs.

The application is intended for use with sensitive student/child datasets.

The application must be usable by a non-technical user through a normal web browser. The user should not need to install any software to use the deployed application.

The application should be simple, transparent, predictable, and privacy-conscious.

---

# 2. Core principles

These are non-negotiable requirements.

### Privacy first

The application must not deliberately persist uploaded or processed student data.

Do NOT:

* save uploaded files to disk
* save processed files to disk
* create an uploads directory
* create an output directory
* use a database
* save identifier mappings
* save student names or IDs
* send data to external APIs
* send data to an LLM
* use external PII-processing services
* log cell values
* log personally identifying information
* retain datasets between sessions

Process uploaded data in memory.

Use in-memory objects such as pandas DataFrames and `BytesIO`.

The application should not deliberately write either the source dataset or processed dataset to persistent storage.

Do not claim that this provides an absolute guarantee that data cannot exist temporarily in the underlying hosting infrastructure. The application itself must simply avoid deliberately persisting the data.

---

# 3. Terminology

The application should be called:

**Student Data De-identification Tool**

Use:

* **De-identification** for the overall process.
* **Pseudonymisation** when replacing values with anonymous-looking identifiers.
* **Delete** when removing a column entirely.

Do not claim that the application guarantees complete legal anonymisation.

The UI should contain a short disclaimer:

> De-identification removes or replaces the identifiers selected by the user. It does not guarantee that an individual cannot be re-identified using other information in the dataset. Users are responsible for reviewing the resulting dataset before sharing it.

Also make clear that sequential IDs are pseudonymous identifiers and are not a guarantee of complete anonymity.

---

# 4. Input files

Accept only:

* `.csv`
* `.xlsx`

Do not support:

* `.xls`
* `.xlsm`
* `.xlsb`
* other file formats

For `.xlsx` files:

* The workbook must contain exactly one worksheet.
* If it contains more than one worksheet, reject the file.
* Do not allow the user to select one sheet from a multi-sheet workbook.
* Reset the upload/process state after this error.

Use a clear error message:

> Excel files must contain exactly one worksheet. Please upload a workbook containing only one worksheet.

CSV files are treated as single-table datasets.

---

# 5. File and user independence

Every uploaded file and every user session is completely independent.

Do NOT:

* remember previous uploads
* compare uploads
* retain mappings between uploads
* maintain global student IDs
* create accounts
* create persistent user identities
* attempt to make identifiers consistent between separate uploads

Every upload starts from scratch.

If the same student appears in two different files, the application does not need to recognise that they are the same student.

---

# 6. Dataset preview

After a valid file is uploaded, show:

* File name
* Number of rows
* Number of columns
* Column names
* First 10 rows

Do not unnecessarily display the entire dataset.

The preview is intended to help the user understand the structure of the dataset and identify columns containing personal/student identifiers.

---

# 7. Long and wide/short format

The user must explicitly select the dataset format.

Options:

### Long format

Explain:

> Long format means the same student can appear in multiple rows, usually because each row represents an assessment, observation, item, time point, or event.

Example:

| Student ID | Assessment | Subject | Score |
| ---------- | ---------- | ------- | ----: |
| 101        | Baseline   | Reading |    20 |
| 101        | Midline    | Reading |    35 |
| 101        | Endline    | Reading |    48 |
| 102        | Baseline   | Reading |    25 |

### Wide/short format

Explain:

> Wide format means a student generally appears in one row, with different measurements stored in separate columns.

Example:

| Student ID | Baseline Score | Midline Score | Endline Score |
| ---------- | -------------: | ------------: | ------------: |
| 101        |             20 |            35 |            48 |
| 102        |             25 |            40 |            51 |

The user must select one.

IMPORTANT:

The long/wide selection is informational.

Do NOT use it to:

* combine columns
* combine rows
* infer student identity
* create composite identifiers
* alter the pseudonymisation logic
* reshape the dataset

---

# 8. Identifier column detection

The application may identify likely identifier columns and suggest them to the user.

Potential examples include:

* Student Name
* Student ID
* Child Name
* Child ID
* Learner Name
* Learner ID
* Parent Name
* Parent Phone
* Phone
* Email
* Address
* Registration Number
* etc.

Detection should use simple, transparent rules such as column-name matching.

Do NOT automatically modify any detected column.

The user must explicitly choose which columns to modify.

The application should clearly distinguish between:

* suggested columns
* user-selected columns

The user always has final control.

---

# 9. Column actions

For every selected column, the user chooses exactly one action:

### Delete

Remove the entire column from the output.

### Pseudonymise

Replace values with sequential anonymous IDs.

The user must be able to select different actions for different columns.

Example:

```text
Student Name → Pseudonymise
Student ID   → Pseudonymise
Parent Phone → Delete
School       → Keep
Grade        → Keep
Score        → Keep
```

---

# 10. CRITICAL: independent column processing

Each selected column must be processed **completely independently from every other column**.

This is one of the most important requirements of the application.

Never combine columns to determine identity.

Never create composite identifiers.

Never combine:

```text
Student Name + Student ID
```

or:

```text
Student Name + School
```

or any other combination of columns.

Each pseudonymised column gets its own completely independent mapping.

Example:

Input:

| Student Name | Student ID | Score |
| ------------ | ---------- | ----: |
| Rahul        | 123        |    50 |
| Aisha        | 456        |    60 |
| Rahul        | 123        |    70 |

Student Name mapping:

```text
Rahul → ANON_00001
Aisha → ANON_00002
```

Student ID mapping:

```text
123 → ANON_00001
456 → ANON_00002
```

These are two completely separate mappings.

The fact that both happen to use the same sequential numbers is coincidental.

The application must never use the relationship between the two columns.

---

# 11. Sequential IDs

Use simple sequential identifiers.

Format:

```text
ANON_00001
ANON_00002
ANON_00003
...
```

Do NOT use:

* random IDs
* hashes
* original student IDs
* encrypted student IDs
* composite identifiers

Each pseudonymised column starts independently at:

```text
ANON_00001
```

For example:

```text
Student Name:
Rahul → ANON_00001
Aisha → ANON_00002

Student ID:
123 → ANON_00001
456 → ANON_00002
```

Sequential IDs are intentional.

The UI disclaimer should make clear that sequential pseudonymous IDs do not guarantee complete anonymity.

---

# 12. Repeated values

Repeated values within the same column must receive the same anonymous ID.

Example:

```text
Rahul
Aisha
Rahul
Rahul
Mohammed
Aisha
```

becomes:

```text
ANON_00001
ANON_00002
ANON_00001
ANON_00001
ANON_00003
ANON_00002
```

This applies independently to every pseudonymised column.

---

# 13. Missing values

Missing, null, or blank values must remain missing.

Do not assign anonymous IDs to missing values.

Example:

```text
Rahul
blank
Aisha
blank
```

becomes:

```text
ANON_00001
blank
ANON_00002
blank
```

---

# 14. Long-format behaviour

In long-format data, the same student may appear in multiple rows.

Repeated values in the selected identifier column must receive the same anonymous ID.

Do not:

* merge rows
* aggregate rows
* remove duplicate rows
* reshape the dataset
* otherwise alter the structure of the dataset

The only changes should be the explicit column actions selected by the user.

---

# 15. Wide-format behaviour

In wide-format data, process the selected identifier columns exactly as they appear.

Do not:

* reshape the dataset
* split columns
* merge columns
* infer relationships between identifier columns
* alter other columns

---

# 16. Preserve all non-selected data

Columns that the user chooses to keep must remain unchanged as far as reasonably possible.

Do not unnecessarily modify:

* scores
* grades
* assessment results
* dates
* categorical variables
* numerical variables
* school names
* teacher names
* other non-selected columns

Do not perform additional de-identification unless the user explicitly selects the column.

---

# 17. Final review

Before processing, show a final review.

Example:

### Columns to pseudonymise

* Student Name
* Student ID

### Columns to delete

* Parent Phone

### Columns that will remain unchanged

* School
* Grade
* Gender
* Assessment
* Score

The user must explicitly click:

**De-identify Dataset**

before processing begins.

---

# 18. Download behaviour

Never automatically download the output.

After processing:

Show a completion message.

Show useful summary information such as:

* rows processed
* original number of columns
* columns deleted
* columns pseudonymised
* unique values pseudonymised per selected column

Then provide:

**Download De-identified Dataset**

The output should only download when the user explicitly clicks the button.

---

# 19. Output format

If input is `.xlsx`:

* output `.xlsx`

If input is `.csv`:

* output `.csv`

Use in-memory objects such as `BytesIO`.

Do not write the generated file to disk.

---

# 20. Error handling

Handle at least:

### Unsupported file

> Please upload a CSV or Excel (.xlsx) file.

### Multiple Excel worksheets

> Excel files must contain exactly one worksheet. Please upload a workbook containing only one worksheet.

Reset the relevant workflow state.

### Empty file

> The uploaded file appears to be empty.

### Empty dataset

> The dataset does not contain any rows.

### No columns

> The dataset does not contain any columns.

### No selected actions

> Please select at least one column to delete or pseudonymise.

### Processing error

Show a clear, user-friendly error.

Never expose raw dataset values in error messages.

Never log sensitive values.

---

# 21. UI philosophy

Keep the interface simple and professional.

The intended workflow is:

## Student Data De-identification Tool

### Step 1 — Upload dataset

### Step 2 — Review dataset

### Step 3 — Select dataset format

### Step 4 — Select columns and actions

### Step 5 — Review changes

### Step 6 — De-identify

### Step 7 — Download

Do not add unnecessary features.

Do not add authentication.

Do not add a database.

Do not add cloud storage.

---

# 22. Technology

Use:

* Python
* Streamlit
* pandas
* openpyxl

Only add another dependency if there is a clear technical reason.

The application should run with:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The deployed application must be usable through a normal web browser without requiring the end user to install Python, Streamlit, or any other software.

---

# 23. Suggested project structure

```text
student-data-deidentifier/
│
├── CLAUDE.md
├── app.py
├── requirements.txt
├── README.md
│
├── anonymizer/
│   ├── __init__.py
│   ├── file_handler.py
│   ├── detector.py
│   ├── anonymizer.py
│   └── validator.py
│
└── tests/
    ├── test_file_handler.py
    ├── test_anonymizer.py
    └── test_validator.py
```

Keep the implementation simple and modular.

---

# 24. Testing requirements

Tests must cover:

1. Basic pseudonymisation
2. Repeated values
3. Missing values
4. Independent column mappings
5. Column deletion
6. Mixed delete + pseudonymise actions
7. CSV input
8. Single-sheet Excel input
9. Multi-sheet Excel rejection
10. Long-format data
11. Wide-format data
12. No selected columns
13. Preservation of non-selected columns
14. Output format matching input format

The core de-identification logic must be testable independently from the Streamlit UI.

---

# 25. Things Claude must NOT do without explicit instruction

Do not:

* change the de-identification rules
* combine columns
* combine rows
* create composite identifiers
* create persistent mappings
* retain mappings between uploads
* automatically delete columns
* automatically pseudonymise columns
* automatically download files
* store uploaded files
* store processed files
* add an external API
* add an LLM
* add authentication
* add a database
* add cloud storage
* add unnecessary dependencies
* add features that are not part of this specification

If a requirement appears ambiguous, ask before making a significant architectural change.

The priority is:

**simple + predictable + privacy-conscious + reliable.**