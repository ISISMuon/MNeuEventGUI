"""Example filter sets used by tests.

These are turned into JSON files for testing
by the setup function `handle_test_json_data`
in conftest.py.

Each one is a BatchData object with a single
filter set, which holds the filters.
"""
from MNeuEventLib import BatchData

from tests.data_paths import FILE

N_SPEC = 64


def _batch():
    """
    Create a BatchData object with one empty filter set.
    :returns: the BatchData object
    """
    return BatchData(FILE, N_SPEC, 1)

load_filter = _batch()
load_filter.set_time_type(0, 'include')
load_filter.add_time_filter(0, 'first', 0.01, 0.02)
load_filter.add_time_filter(0, 'second', 0.05, 0.06)
load_filter.add_log_filter(0, 'log_default_1', 'Temp', 0.0044, 0.163)
load_filter.set_amps_baseline(0, 3.14)
load_filter.set_histogram_settings(0, 0.5, 15.22, 1024)
