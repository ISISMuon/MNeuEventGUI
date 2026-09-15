"""Pytest setup and teardown."""
import os
from pathlib import Path

import pytest

from tests.data_files.filters import (filter_exclude,
                                     filter_include,
                                     load_filter,
                                     load_bad_filter)

pwd = Path(os.path.abspath(__file__))
data_dir = Path(pwd.parent, "data_files")

@pytest.fixture(scope="session", autouse=True)
def handle_test_json_data():
    """
    Create and remove the test data files used by tests.
    """
    # this happens at start of pytest session
    filter_exclude.write_json(data_dir / "filter_exclude.json")
    filter_include.write_json(data_dir / "filter_include.json")
    load_filter.write_json(data_dir / "load_filter.json")
    load_bad_filter.write_json(data_dir / "load_bad_filter.json")
    load_bad_filter.write_json(data_dir / "script_load_filter.json")

    yield  # run tests

    # this happens at end of pytest session; clean up json files
    (data_dir / "filter_exclude.json").unlink()
    (data_dir / "filter_include.json").unlink()
    (data_dir / "load_filter.json").unlink()
    (data_dir / "load_bad_filter.json").unlink()
    (data_dir / "script_load_filter.json").unlink()

