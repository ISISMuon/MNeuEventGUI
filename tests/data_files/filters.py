"""Example filter sets used by tests.

These are turned into JSON files for testing
by the setup function `handle_test_json_data`
in conftest.py.
"""
from MuonDataLib.filters import (Filters,
                                 Filter,
                                 PeakProperty,
                                 TimeFilters,
                                 HistogramSettings)

filter_exclude = Filters(
    time_filters = TimeFilters(
        keep_filters = [Filter('default_1', 200, 400),
                        Filter('default_2', 600, 1100)]
        )
    )

filter_include = Filters(
    time_filters = TimeFilters(
        keep_filters = [Filter('default_1', 200, 400),
                        Filter('default_2', 600, 1100)]
        )
    )

load_filter = Filters(
    time_filters = TimeFilters(
        keep_filters = [Filter('first', 0.01, 0.02),
                        Filter('second', 0.05, 0.06)]
        ),
    sample_log_filters = [Filter('Temp', 0.0044, 0.163)],
    peak_property = PeakProperty(3.14),
    histogram_settings = HistogramSettings(
        min_time = 0.5,
        max_time = 15.22,
        num_bins = 1024
        )
    )

load_bad_filter = Filters(
    time_filters = TimeFilters(
        keep_filters = [Filter('first', 0.01, 0.02),
                        Filter('second', 0.05, 0.06)],
        remove_filters = [Filter('one', 1, 2),
                          Filter('two', 5, 7)]
        ),
    sample_log_filters = [Filter('Temp', 0.0044, 0.163)],
    peak_property = PeakProperty(3.14)
    )


