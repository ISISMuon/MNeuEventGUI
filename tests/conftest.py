"""Pytest setup and teardown."""
import os
from pathlib import Path

import pytest

from tests.data_files.filters import load_filter
from tests.data_paths import FILTER

pwd = Path(os.path.abspath(__file__))
data_dir = Path(pwd.parent, "data_files")

@pytest.fixture(scope="session", autouse=True)
def handle_test_json_data():
    """
    Create and remove the test data files used by tests.
    """
    # this happens at start of pytest session
    load_filter.save_filters(0, FILTER)


    yield  # run tests

    # this happens at end of pytest session; clean up json files
    (data_dir / "load_filter.json").unlink()
