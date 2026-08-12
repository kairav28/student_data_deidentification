import pytest

from anonymizer.validator import NoActionsSelectedError, validate_column_actions


def test_no_actions_selected_raises_when_all_kept():
    with pytest.raises(NoActionsSelectedError):
        validate_column_actions({"Student Name": "keep", "Score": "keep"})


def test_no_actions_selected_raises_on_empty_dict():
    with pytest.raises(NoActionsSelectedError):
        validate_column_actions({})


def test_at_least_one_action_passes_validation():
    validate_column_actions({"Student Name": "pseudonymise", "Score": "keep"})
