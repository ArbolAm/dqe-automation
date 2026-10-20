import pytest
import re


def test_file_not_empty(csv_file_path):
    df = csv_file_path
    assert not df.empty, "file empty."


@pytest.mark.validate_csv
@pytest.mark.xfail(reason="expected fail: duplicate rows", strict=True)
def test_duplicates(csv_file_path):
    df = csv_file_path
    assert not df.duplicated().any(), "duplicates present."


@pytest.mark.validate_csv
def test_validate_schema(csv_file_path, validate_schema):
    df = csv_file_path
    expected_header = ["id", "name", "age", "email", "is_active"]
    validate_schema(df.columns, expected_header)


@pytest.mark.validate_csv
@pytest.mark.skip(reason="skipping age validation as requested")
def test_age_column_valid(csv_file_path):
    df = csv_file_path
    for age in df["age"]:
        assert 0 <= age <= 100, f"invalid age found: {age}"


@pytest.mark.validate_csv
def test_email_column_valid(csv_file_path):
    df = csv_file_path
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    for email in df["email"]:
        assert bool(re.match(email_regex, str(email))), f"invalid email format: {email}"


@pytest.mark.validate_csv
@pytest.mark.parametrize(
    "id_val, expected_is_active", [(1, False), (2, True)]
)
def test_active_players(csv_file_path, id_val, expected_is_active):
    df = csv_file_path
    matching_rows = df[df["id"] == id_val]
    if matching_rows.empty:
        pytest.skip(f"row with id {id_val} not present in dataset.")

    actual_is_active = matching_rows.iloc[0]["is_active"]
    assert actual_is_active == expected_is_active


def test_active_player(csv_file_path):
    df = csv_file_path
    matching_rows = df[df["id"] == 2]
    if matching_rows.empty:
        pytest.skip("row with id 2 not present in dataset.")

    actual_is_active = matching_rows.iloc[0]["is_active"]
    assert actual_is_active is True
