"""Student Data De-identification Tool — Streamlit UI.

All processing happens in memory against the uploaded file's bytes and a
pandas DataFrame held in Streamlit's session state. Nothing is written to
disk, no database is used, and no data leaves this process.

Layout: a single, compact page split into a left half (upload, dataset
preview, per-column actions, format selection) and a right half
(processed-data preview and download), with a "De-identify Dataset"
button in between. Processing only happens when that button is clicked —
changing a selection does not reprocess automatically.
"""
from __future__ import annotations

import streamlit as st

from anonymizer.anonymizer import process_dataframe
from anonymizer.detector import suggest_identifier_columns
from anonymizer.file_handler import get_extension, load_dataset, output_filename, write_dataset
from anonymizer.validator import DeidentificationError, NoActionsSelectedError, validate_column_actions

st.set_page_config(page_title="Student Data De-identification Tool", layout="wide")

# Compact spacing/typography. Hooks are Streamlit's documented data-testid
# attributes and the st-key-<key> class it generates for keyed containers,
# not obfuscated internals, so this should stay stable across versions.
COMPACT_CSS = """
<style>
[data-testid="stMainBlockContainer"] {
    padding: 1rem 1rem 2rem 1rem !important;
}
h1 {
    font-size: 1.4rem !important;
    margin-bottom: 0.2rem !important;
}
[data-testid="stAlert"] {
    padding: 0.4rem 0.75rem !important;
}
[data-testid="stAlert"] p {
    font-size: 0.8rem !important;
    margin-bottom: 0 !important;
}
.st-key-column_actions_row [data-testid="stHorizontalBlock"] {
    overflow-x: auto;
    flex-wrap: nowrap !important;
    padding-bottom: 0.3rem;
}
.st-key-column_actions_row [data-testid="stColumn"] {
    min-width: 110px;
    flex: 0 0 auto !important;
}
</style>
"""

DISCLAIMER = (
    "De-identification removes or replaces the identifiers selected by the user. "
    "It does not guarantee that an individual cannot be re-identified using other "
    "information in the dataset, and sequential pseudonymous IDs (e.g. ANON_00001) "
    "do not guarantee complete anonymity. Users are responsible for reviewing the "
    "resulting dataset before sharing it."
)

FORMAT_LONG = "Long format"
FORMAT_WIDE = "Wide/short format"
FORMAT_HELP = (
    "**Long**: the same student can appear in multiple rows (e.g. one row per "
    "assessment or time point). **Wide/short**: each student appears in one row, "
    "with separate columns per measurement (e.g. baseline/midline/endline score "
    "columns). This choice is informational only and does not change how columns "
    "are processed."
)

ACTION_KEEP = "Keep"
ACTION_DELETE = "Delete"
ACTION_PSEUDONYMISE = "Pseudonymise"
ACTION_MAP = {ACTION_DELETE: "delete", ACTION_PSEUDONYMISE: "pseudonymise"}

_WORKFLOW_STATE_KEYS = (
    "df", "extension", "original_filename", "format_choice",
    "processed_actions", "result_df", "output_bytes", "output_mime",
    "output_name", "summary",
)


def reset_workflow_state() -> None:
    """Clear all state derived from a previously uploaded file.

    Called whenever a new file is uploaded (or an invalid one is rejected)
    so that no selection, mapping, or result from a prior file can leak
    into the next one.
    """
    for key in _WORKFLOW_STATE_KEYS:
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        if key.startswith("action_"):
            del st.session_state[key]


def render_upload_and_input(container) -> None:
    """Left half: upload, dataset preview, per-column actions, format selection."""
    with container:
        upload_col, meta_col = st.columns([1.2, 2], vertical_alignment="center")
        with upload_col:
            uploaded_file = st.file_uploader(
                "Upload dataset",
                type=["csv", "xlsx"],
                label_visibility="collapsed",
            )

        if uploaded_file is None:
            st.session_state.pop("current_file_id", None)
            reset_workflow_state()
            return

        file_id = (uploaded_file.name, uploaded_file.size)
        if st.session_state.get("current_file_id") != file_id:
            reset_workflow_state()
            st.session_state["current_file_id"] = file_id

            file_bytes = uploaded_file.getvalue()
            try:
                loaded_df = load_dataset(file_bytes, uploaded_file.name)
            except DeidentificationError as exc:
                with meta_col:
                    st.error(str(exc))
                st.session_state.pop("current_file_id", None)
                return

            st.session_state["df"] = loaded_df
            st.session_state["extension"] = get_extension(uploaded_file.name)
            st.session_state["original_filename"] = uploaded_file.name

        if "df" not in st.session_state:
            return

        df = st.session_state["df"]

        with meta_col:
            st.caption(
                f"**{st.session_state['original_filename']}** — "
                f"{len(df)} rows, {len(df.columns)} columns"
            )

        st.dataframe(df.head(10), height=200, width="stretch")

        st.write("**Column actions** (Keep / Delete / Pseudonymise)")
        suggested = set(suggest_identifier_columns(df.columns))
        with st.container(key="column_actions_row", border=True):
            action_cols = st.columns(len(df.columns))
            for action_col, column in zip(action_cols, df.columns):
                with action_col:
                    st.selectbox(
                        str(column),
                        [ACTION_KEEP, ACTION_DELETE, ACTION_PSEUDONYMISE],
                        key=f"action_{column}",
                        help="Suggested identifier column, based on its name."
                        if column in suggested
                        else None,
                    )

        st.segmented_control(
            "Dataset format",
            [FORMAT_LONG, FORMAT_WIDE],
            key="format_choice",
            default=None,
            help=FORMAT_HELP,
        )


def render_process_button(container) -> None:
    """Middle: the single explicit action that triggers de-identification."""
    with container:
        df = st.session_state.get("df")
        st.write("")
        clicked = st.button(
            "De-identify Dataset",
            width="stretch",
            disabled=df is None,
            help="Process the dataset in memory using the selections on the left."
            if df is not None
            else "Upload a dataset first.",
        )

        if not clicked:
            if st.session_state.get("result_df") is not None and _selections_changed():
                st.caption("Selections changed — click again to update.")
            return

        if df is None:
            return

        format_choice = st.session_state.get("format_choice")
        if not format_choice:
            st.error("Please select a dataset format before processing.")
            return

        column_actions_ui = {
            column: st.session_state.get(f"action_{column}", ACTION_KEEP) for column in df.columns
        }
        column_actions = {
            column: ACTION_MAP[choice]
            for column, choice in column_actions_ui.items()
            if choice in ACTION_MAP
        }

        try:
            validate_column_actions(column_actions)
        except NoActionsSelectedError as exc:
            st.error(str(exc))
            return

        result_df, summary = process_dataframe(df, column_actions)
        extension = st.session_state["extension"]
        output_bytes, mime_type = write_dataset(result_df, extension)

        st.session_state["processed_actions"] = dict(column_actions)
        st.session_state["result_df"] = result_df
        st.session_state["output_bytes"] = output_bytes
        st.session_state["output_mime"] = mime_type
        st.session_state["output_name"] = output_filename(
            st.session_state["original_filename"], extension
        )
        st.session_state["summary"] = summary


def _selections_changed() -> bool:
    """Whether column actions have changed since the dataset was last processed."""
    df = st.session_state.get("df")
    if df is None or st.session_state.get("processed_actions") is None:
        return False
    current = {
        column: ACTION_MAP[st.session_state.get(f"action_{column}", ACTION_KEEP)]
        for column in df.columns
        if st.session_state.get(f"action_{column}", ACTION_KEEP) in ACTION_MAP
    }
    return current != st.session_state["processed_actions"]


def render_processed_output(container) -> None:
    """Right half: download button (above the preview) and processed-data preview."""
    with container:
        st.write("**Processed data**")

        if st.session_state.get("result_df") is None:
            st.info("Configure columns on the left, then click \"De-identify Dataset\".")
            return

        summary = st.session_state["summary"]

        st.download_button(
            "Download De-identified Dataset",
            data=st.session_state["output_bytes"],
            file_name=st.session_state["output_name"],
            mime=st.session_state["output_mime"],
            width="stretch",
        )

        st.caption(
            f"{summary['rows']} rows processed • "
            f"{len(summary['columns_deleted'])} column(s) deleted • "
            f"{len(summary['columns_pseudonymised'])} column(s) pseudonymised"
        )
        if summary["columns_deleted"]:
            st.caption("Deleted: " + ", ".join(summary["columns_deleted"]))
        if summary["columns_pseudonymised"]:
            details = ", ".join(
                f"{col} ({summary['unique_values_pseudonymised'].get(col, 0)} unique)"
                for col in summary["columns_pseudonymised"]
            )
            st.caption("Pseudonymised: " + details)

        st.dataframe(st.session_state["result_df"].head(10), height=200, width="stretch")


def main() -> None:
    st.markdown(COMPACT_CSS, unsafe_allow_html=True)
    st.title("Student Data De-identification Tool")
    st.info(DISCLAIMER)

    left_col, mid_col, right_col = st.columns([5, 1.2, 5], gap="medium", vertical_alignment="center")

    render_upload_and_input(left_col)
    render_process_button(mid_col)
    render_processed_output(right_col)


if __name__ == "__main__":
    main()
