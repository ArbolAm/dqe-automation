import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime

FILE_PATH = "src/data/data.csv"


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_sessionstart(session):
    service = getattr(session.config, "py_test_service", None)
    if service is not None:
        service._config.rp_launch = datetime.now().strftime("my_launch_%Y%m%d_%H%M%S")
    yield


# Fixture to read the CSV file
@pytest.fixture(scope="session")
def csv_file_path():
    custom_path = FILE_PATH
    path = Path(__file__).parent.parent / custom_path
    assert path.exists(), f"CSV file not found at {path}"
    return pd.read_csv(path)


# Fixture to validate the schema of the file
@pytest.fixture(scope="session")
def validate_schema():
    def _validate(actual_sch, expected_sch):
        assert list(actual_sch) == expected_sch, f"schema mismatch! exp: {expected_sch}, got: {list(actual_sch)}"
        return True
    return _validate


# Pytest hook to mark unmarked tests with a custom mark
def pytest_collection_modifyitems(items):
    for item in items:
        if not item.own_markers:
            item.add_marker(pytest.mark.unmarked)
