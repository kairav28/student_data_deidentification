import pandas as pd

from anonymizer.anonymizer import process_dataframe, pseudonymise_column


def test_basic_pseudonymisation():
    series = pd.Series(["Rahul", "Aisha"])
    result, mapping = pseudonymise_column(series)
    assert list(result) == ["ANON_00001", "ANON_00002"]
    assert mapping == {"Rahul": "ANON_00001", "Aisha": "ANON_00002"}


def test_repeated_values_get_same_id():
    series = pd.Series(["Rahul", "Aisha", "Rahul", "Rahul", "Mohammed", "Aisha"])
    result, _ = pseudonymise_column(series)
    assert list(result) == [
        "ANON_00001", "ANON_00002", "ANON_00001",
        "ANON_00001", "ANON_00003", "ANON_00002",
    ]


def test_missing_values_stay_missing():
    series = pd.Series(["Rahul", None, "Aisha", ""])
    result, _ = pseudonymise_column(series)
    assert result[0] == "ANON_00001"
    assert pd.isna(result[1])
    assert result[2] == "ANON_00002"
    assert result[3] == ""


def test_independent_column_mappings():
    df = pd.DataFrame({
        "Student Name": ["Rahul", "Aisha", "Rahul"],
        "Student ID": [123, 456, 123],
        "Score": [50, 60, 70],
    })
    result, summary = process_dataframe(df, {
        "Student Name": "pseudonymise",
        "Student ID": "pseudonymise",
    })
    assert list(result["Student Name"]) == ["ANON_00001", "ANON_00002", "ANON_00001"]
    assert list(result["Student ID"]) == ["ANON_00001", "ANON_00002", "ANON_00001"]
    assert list(result["Score"]) == [50, 60, 70]
    assert summary["unique_values_pseudonymised"] == {"Student Name": 2, "Student ID": 2}


def test_independent_mappings_do_not_use_composite_identity():
    # Same person (row 0) has a name shared with row 2's ID-holder in a way
    # that would collide if columns were combined. Each column must still
    # only look at its own values.
    df = pd.DataFrame({
        "Student Name": ["Rahul", "Aisha", "Mohammed"],
        "Student ID": [999, 999, 111],
    })
    result, _ = process_dataframe(df, {
        "Student Name": "pseudonymise",
        "Student ID": "pseudonymise",
    })
    assert list(result["Student Name"]) == ["ANON_00001", "ANON_00002", "ANON_00003"]
    assert list(result["Student ID"]) == ["ANON_00001", "ANON_00001", "ANON_00002"]


def test_column_deletion():
    df = pd.DataFrame({"Parent Phone": ["111", "222"], "Score": [1, 2]})
    result, summary = process_dataframe(df, {"Parent Phone": "delete"})
    assert "Parent Phone" not in result.columns
    assert list(result.columns) == ["Score"]
    assert summary["columns_deleted"] == ["Parent Phone"]


def test_mixed_delete_and_pseudonymise():
    df = pd.DataFrame({
        "Student Name": ["Rahul", "Aisha"],
        "Parent Phone": ["111", "222"],
        "School": ["A", "B"],
    })
    actions = {"Student Name": "pseudonymise", "Parent Phone": "delete"}
    result, summary = process_dataframe(df, actions)
    assert list(result.columns) == ["Student Name", "School"]
    assert list(result["Student Name"]) == ["ANON_00001", "ANON_00002"]
    assert list(result["School"]) == ["A", "B"]
    assert summary["columns_deleted"] == ["Parent Phone"]
    assert summary["columns_pseudonymised"] == ["Student Name"]


def test_preservation_of_non_selected_columns():
    df = pd.DataFrame({
        "Student Name": ["Rahul", "Aisha"],
        "Grade": [5, 6],
        "Score": [88.5, 92.0],
    })
    result, _ = process_dataframe(df, {"Student Name": "pseudonymise"})
    assert list(result["Grade"]) == [5, 6]
    assert list(result["Score"]) == [88.5, 92.0]


def test_long_format_repeated_student_rows_not_merged():
    df = pd.DataFrame({
        "Student ID": [101, 101, 101, 102],
        "Assessment": ["Baseline", "Midline", "Endline", "Baseline"],
        "Score": [20, 35, 48, 25],
    })
    result, _ = process_dataframe(df, {"Student ID": "pseudonymise"})
    assert len(result) == len(df)
    assert list(result["Student ID"]) == [
        "ANON_00001", "ANON_00001", "ANON_00001", "ANON_00002",
    ]
    assert list(result["Assessment"]) == list(df["Assessment"])
    assert list(result["Score"]) == list(df["Score"])


def test_wide_format_multiple_identifier_columns_independent():
    df = pd.DataFrame({
        "Student ID": [101, 102],
        "Parent Phone": ["555-1111", "555-2222"],
        "Baseline Score": [20, 25],
    })
    result, _ = process_dataframe(df, {
        "Student ID": "pseudonymise",
        "Parent Phone": "pseudonymise",
    })
    assert list(result["Student ID"]) == ["ANON_00001", "ANON_00002"]
    assert list(result["Parent Phone"]) == ["ANON_00001", "ANON_00002"]
    assert list(result["Baseline Score"]) == [20, 25]


def test_no_columns_selected_leaves_dataframe_unchanged():
    df = pd.DataFrame({"Score": [1, 2, 3]})
    result, summary = process_dataframe(df, {})
    assert list(result.columns) == ["Score"]
    assert list(result["Score"]) == [1, 2, 3]
    assert summary["columns_deleted"] == []
    assert summary["columns_pseudonymised"] == []
