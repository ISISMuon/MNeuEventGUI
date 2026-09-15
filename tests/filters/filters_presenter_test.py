import unittest
from unittest import mock
from MuonDataLib.GUI.filters.presenter import FilterPresenter
from MuonDataLib.test_helpers.unit_test import TestHelper
from MuonDataLib.data.loader.load_events import load_events
from MuonDataLib.filters import (Filter, Filters, PeakProperty,
                                      TimeFilters, HistogramSettings)
import numpy as np
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from data_paths import FILE  # noqa: E402


TT = '_time-table'
LT = '_log-table'
DEFAULT_HIST = (0., 32.768, 2048)  # default histogram settings


class FilterPresenterTest(TestHelper):

    def setUp(self):
        self.presenter = FilterPresenter()

    def test_show_file_match(self):
        name = 'test.json'
        """
        lets use fake values (should be dicts,
        but just checks they match)
        """
        self.presenter._time_file_data = 'time'
        self.presenter._log_file_data = 'log'
        self.presenter._amp_file_data = 2
        self.presenter._hist_data = HistogramSettings(
            min_time = 0.,
            max_time = 1.,
            num_bins = 2,
                )

        self.assertFalse(self.presenter.show_file(name, 'time', 'log', 2,
                                                  0., 1., 2))

    def test_show_file_match_amp_fails(self):
        name = 'test.json'
        """
        lets use fake values (should be dicts,
        but just checks they match)
        """
        self.presenter._time_file_data = 'time'
        self.presenter._log_file_data = 'log'
        self.presenter._amp_file_data = 2
        self.presenter._hist_data = HistogramSettings(
            min_time = 0.,
            max_time = 1.,
            num_bins = 2,
                )

        self.assertTrue(self.presenter.show_file(name, 'time', 'log', 4,
                                                 0., 1., 2))

    def test_show_file_time_match(self):
        name = 'test.json'
        """
        lets use fake values (should be dicts,
        but just checks they match)
        """
        self.presenter._time_file_data = 'time'
        self.presenter._log_file_data = 'log'
        self.presenter._amp_file_data = 2
        self.presenter._hist_data = HistogramSettings(
            min_time = 0.,
            max_time = 1.,
            num_bins = 2,
                )

        self.assertTrue(self.presenter.show_file(name, 'time', 'new', 2,
                                                 0., 1., 2))

    def test_show_file_log_match(self):
        name = 'test.json'
        """
        lets use fake values (should be dicts,
        but it just checks the values match)
        """
        self.presenter._time_file_data = 'time'
        self.presenter._log_file_data = 'log'
        self.presenter._amp_file_data = 2
        self.presenter._hist_data = HistogramSettings(
            min_time = 0.,
            max_time = 1.,
            num_bins = 2,
                )

        self.assertTrue(self.presenter.show_file(name, 'new', 'log', 2,
                                                 0., 1., 2.))

    def test_show_file_hist_fails(self):
        """
        Test that histogram settings changing causes a non-match.
        """
        name = "test.json"
        self.presenter._time_file_data = 'time'
        self.presenter._log_file_data = 'log'
        self.presenter._amp_file_data = 2
        self.presenter._hist_data = HistogramSettings(
            min_time = 0.,
            max_time = 1.,
            num_bins = 2,
                )

        for hist_settings in [
            (1., 1., 2),
            (0., 2., 2),
            (0., 1., 5),
            ]:
            self.assertTrue(
                self.presenter.show_file(name, 'new', 'log', 2, *hist_settings)
                )
    def test_show_file_no_match(self):
        name = 'test.json'
        """
        lets use fake values (should be dicts,
        but just checks they match)
        """
        self.presenter._time_file_data = 'time'
        self.presenter._log_file_data = 'log'
        self.presenter._amp_file_data = 2
        self.presenter._hist_data = HistogramSettings(
            min_time = 0.,
            max_time = 1.,
            num_bins = 2,
                )

        self.assertTrue(self.presenter.show_file(name, 'unit', 'test', 3,
                                                 5., 6.5, 7))

    def test_headers(self):
        self.assertEqual(len(self.presenter.headers), 3)

    def test_set_data(self):
        class MockData(object):
            def __init__(self):
                self._dict = {'logs': 'log data'}

            def get_frame_start_times(self):
                return [1, 2, 6]

        data = MockData()

        self.presenter._time.set_time_range = mock.Mock()

        self.presenter.set_data(data)
        self.presenter._time.set_time_range.assert_called_with(1, 6 + 32e-6)
        self.assertEqual(self.presenter._log._logs, 'log data')

    def test_apply_filters_none(self):
        filters = []
        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters(filters,
                                     'Include',
                                     [],
                                     0)
        result = self.presenter._data.report_filters()

        assert result == Filters()

    def test_apply_filters_include(self):
        filters = [{'Name' + TT: 'unit',
                    'Start' + TT: 0.1,
                    'End' + TT: 0.5},
                   {'Name' + TT: 'test',
                    'Start' + TT: 0.7,
                    'End' + TT: 1.2}]

        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters(filters,
                                     'Include',
                                     [],
                                     0)
        result = self.presenter._data.report_filters()

        assert result == Filters(
                             time_filters=TimeFilters(
                                 keep_filters=[Filter('unit', 0.1, 0.5),
                                               Filter('test', 0.7, 1.2)]
                             )
                        )

    def test_apply_filters_exclude(self):
        filters = [{'Name' + TT: 'unit',
                    'Start' + TT: 0.1,
                    'End' + TT: 0.5},
                   {'Name' + TT: 'test',
                    'Start' + TT: 0.7,
                    'End' + TT: 1.2}]

        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters(filters,
                                     'Exclude',
                                     [],
                                     0)
        result = self.presenter._data.report_filters()

        assert result == Filters(
                             time_filters=TimeFilters(
                                 remove_filters=[Filter('unit', 0.1, 0.5),
                                                 Filter('test', 0.7, 1.2)]
                             )
                        )

    def test_apply_filters_log_between(self):
        filters = [{'filter' + LT: 'between',
                    'sample' + LT: 'Temp',
                    'y0' + LT: 1,
                    'yN' + LT: 11}]

        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters([],
                                     'Exclude',
                                     filters,
                                     0)
        result = self.presenter._data.report_filters()

        assert result == Filters(
                             sample_log_filters=[Filter('Temp', 1, 11)]
                         )

    def test_apply_filters_log_above(self):
        filters = [{'filter' + LT: 'above',
                    'sample' + LT: 'Temp',
                    'y0' + LT: 4,
                    'yN' + LT: 11}]

        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters([],
                                     'Exclude',
                                     filters,
                                     0)
        result = self.presenter._data.report_filters()
        assert result == Filters(
                             sample_log_filters=[Filter('Temp', 4, -999)]
                         )

    def test_apply_filters_log_below(self):
        filters = [{'filter' + LT: 'below',
                    'sample' + LT: 'Temp',
                    'y0' + LT: 0,
                    'yN' + LT: 7}]

        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters([],
                                     'Exclude',
                                     filters,
                                     0)
        result = self.presenter._data.report_filters()
        assert result == Filters(
                             sample_log_filters=[Filter('Temp', -999, 7)]
                         )

    def test_apply_filters_mix(self):
        times = [{'Name' + TT: 'unit',
                  'Start' + TT: 0.1,
                  'End' + TT: 0.5},
                 {'Name' + TT: 'test',
                  'Start' + TT: 0.7,
                  'End' + TT: 1.2}]

        logs = [{'filter' + LT: 'between',
                 'sample' + LT: 'Temp',
                 'y0' + LT: 2,
                 'yN' + LT: 7}]

        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters(times,
                                     'Exclude',
                                     logs,
                                     0)
        result = self.presenter._data.report_filters()
        assert result == Filters(
                             time_filters=TimeFilters(
                                 remove_filters=[Filter('unit', 0.1, 0.5),
                                                 Filter('test', 0.7, 1.2)]
                             ),
                             sample_log_filters=[Filter('Temp', 2, 7)]
                        )

    def test_update_filters_times(self):
        times = [{'Name' + TT: 'unit',
                  'Start' + TT: 0.1,
                  'End' + TT: 0.5},
                 {'Name' + TT: 'test',
                  'Start' + TT: 0.7,
                  'End' + TT: 1.2}]

        self.presenter._data = load_events(FILE, 64)
        start, stop, msg = self.presenter.update_filters(times,
                                                         'Exclude',
                                                         {},
                                                         0)
        self.assertEqual(msg, '')
        self.assertArrays(start, [0.994])
        self.assertArrays(stop, [1.194])

    def test_update_filters_logs(self):
        logs = [{'filter' + LT: 'between',
                 'sample' + LT: 'Temp',
                 'y0' + LT: 3,
                 'yN' + LT: 7}]

        self.presenter._data = load_events(FILE, 64)
        start, stop, msg = self.presenter.update_filters([],
                                                         'Exclude',
                                                         logs,
                                                         0)
        self.assertEqual(msg, '')
        self.assertArrays(start, [0.994])
        self.assertArrays(stop, [3.174])

    def test_update_filters_None(self):
        self.presenter._data = load_events(FILE, 64)
        start, stop, msg = self.presenter.update_filters([],
                                                         'Exclude',
                                                         [],
                                                         0)
        self.assertEqual(msg, '')
        self.assertArrays(start, [])
        self.assertArrays(stop, [])

    def test_update_filters_mix(self):
        times = [{'Name' + TT: 'unit',
                  'Start' + TT: 0.1,
                  'End' + TT: 0.5},
                 {'Name' + TT: 'test',
                  'Start' + TT: 0.7,
                  'End' + TT: 1.2}]

        logs = [{'filter' + LT: 'between',
                 'sample' + LT: 'Temp',
                 'y0' + LT: 2,
                 'yN' + LT: 7}]

        self.presenter._data = load_events(FILE, 64)
        start, stop, msg = self.presenter.update_filters(times,
                                                         'Exclude',
                                                         logs,
                                                         0)
        self.assertEqual(msg, '')
        self.assertArrays(start, [0.994])
        self.assertArrays(stop, [3.174])

    def test_filters_rm_overlaps(self):
        start, stop = self.presenter.filters_rm_overlaps([3, 4, 5],
                                                         [4.2, 4.5, 6])
        self.assertArrays(start, [3, 5])
        self.assertArrays(stop, [4.5, 6])

    def test_get_log_y_range_between(self):
        log = {'magic': 'between',
               'sample' + LT: 'Temp',
               'y0' + LT: 36,
               'yN' + LT: 37,
               'y_min' + LT: 35,
               'y_max' + LT: 39}

        data = load_events(FILE, 64)
        self.presenter.set_data(data)
        low, high = self.presenter.get_log_y_range(log)
        self.assertEqual(low, 36)
        self.assertEqual(high, 37)

    def test_get_log_y_range_below(self):
        log = {'magic': 'below',
               'sample' + LT: 'Temp',
               'y0' + LT: 36,
               'yN' + LT: 37,
               'y_min' + LT: 35,
               'y_max' + LT: 39}

        data = load_events(FILE, 64)
        self.presenter.set_data(data)
        low, high = self.presenter.get_log_y_range(log)
        self.assertEqual(low, 35)
        self.assertEqual(high, 37)

    def test_get_log_y_range_above(self):
        log = {'magic': 'above',
               'sample' + LT: 'Temp',
               'y0' + LT: 36,
               'yN' + LT: 37,
               'y_min' + LT: 35,
               'y_max' + LT: 39}

        data = load_events(FILE, 64)
        self.presenter.set_data(data)
        low, high = self.presenter.get_log_y_range(log)
        self.assertEqual(low, 36)
        self.assertEqual(high, 39)

    def test_calculate_no_filters(self):
        self.presenter._data = load_events(FILE, 64)
        N_str, err_msg = self.presenter.calculate(1, {}, 'Exclude', [], 0,
                                                  *DEFAULT_HIST)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 64,147')

    def test_calculate_amp_filter(self):
        self.presenter._data = load_events(FILE, 64)
        N_str, err_msg = self.presenter.calculate(1, {}, 'Exclude', [], 2500,
                                                  *DEFAULT_HIST)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 7,944')

    def test_calculate_with_exclude_filter(self):
        self.presenter._data = load_events(FILE, 64)
        filters = [{'Name' + TT: 'unit', 'Start' + TT: 0.1, 'End' + TT: 1.2}]
        N_str, err_msg = self.presenter.calculate(1, filters, 'Exclude', [], 0,
                                                  *DEFAULT_HIST)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 57,653')

    def test_calculate_with_include_filter(self):
        self.presenter._data = load_events(FILE, 64)
        filters = [{'Name' + TT: 'unit', 'Start' + TT: 0.1, 'End' + TT: 1.2}]
        N_str, err_msg = self.presenter.calculate(1, filters, 'Include', [], 0,
                                                  *DEFAULT_HIST)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 5,037')

    def test_calculate_with_log_filter(self):
        self.presenter._data = load_events(FILE, 64)
        log = [{'filter' + LT: 'above',
                'sample' + LT: 'Temp',
                'y0' + LT: 35.5,
                'yN' + LT: 37}]

        N_str, err_msg = self.presenter.calculate(1, [], 'Include', log, 0,
                                                  *DEFAULT_HIST)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 57,481')

    def test_calculate_with_error(self):
        def throw(filters, state, log, amp, hist_settings):
            raise RuntimeError("mock throw")

        self.presenter._data = load_events(FILE, 64)
        self.presenter.apply_filters = mock.Mock(side_effect=throw)
        filters = [{'Name_t': 'unit', 'Start_t': 0.1, 'End_t': 1.2}]
        N_str, err_msg = self.presenter.calculate(1, filters, 'Include', [], 0,
                                                  *DEFAULT_HIST)
        self.assertEqual(err_msg, 'mock throw')
        self.assertEqual(N_str.children,
                         'Number of events: 0')

    def test_load_include(self):
        filters = Filters(
                      peak_property = PeakProperty(1.2),
                      time_filters = TimeFilters(
                          keep_filters=[Filter('unit', 1, 2),
                                        Filter('test', 3, 4)]
                      ),
                      sample_log_filters = [Filter('Temp', 36, 37)],
                      histogram_settings = HistogramSettings(
                          min_time = 3.,
                          max_time = 25.55,
                          num_bins = 1000
                          )
                  )

        _data = load_events(FILE, 64)
        self.presenter.set_data(_data)
        (data, logs, amps, min_time, max_time,
         num_bins, state, headers) = self.presenter.load(filters)
        self.assertEqual(state, 'Include')
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], {'Name' + TT: 'unit',
                                   'Start' + TT: 1,
                                   'End' + TT: 2})
        self.assertEqual(data[1], {'Name' + TT: 'test',
                                   'Start' + TT: 3,
                                   'End' + TT: 4})
        self.assertEqual(logs, [{'Name_log-table': 'log_default_1',
                                 'filter_log-table': 'between',
                                 'magic': 'between',
                                 'sample_log-table': 'Temp',
                                 'y0_log-table': 36,
                                 'yN_log-table': 37,
                                 'y_max_log-table': np.float64(39.0),
                                 'y_min_log-table': np.float64(35.0)}
                                ])
        self.assertEqual(amps, 1.2)
        self.assertEqual(min_time, 3.)
        self.assertEqual(max_time, 25.55)
        self.assertEqual(num_bins, 1000)
        self.assertEqual(len(headers), 3)

    def test_load_exclude(self):
        filters = Filters(
                      peak_property = PeakProperty(1.2),
                      time_filters = TimeFilters(
                          remove_filters=[Filter('more', 5, 6),
                                          Filter('tests', 7, 8)]
                      ),
                      histogram_settings = HistogramSettings(
                          min_time = 3.,
                          max_time = 25.55,
                          num_bins = 1000
                          )
                  )
        (data, logs, amps, min_time, max_time,
         num_bins, state, headers) = self.presenter.load(filters)
        self.assertEqual(state, 'Exclude')
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], {'Name' + TT: 'more',
                                   'Start' + TT: 5,
                                   'End' + TT: 6})
        self.assertEqual(data[1], {'Name' + TT: 'tests',
                                   'Start' + TT: 7,
                                   'End' + TT: 8})
        self.assertEqual(logs, [])
        self.assertEqual(amps, 1.2)
        self.assertEqual(min_time, 3.)
        self.assertEqual(max_time, 25.55)
        self.assertEqual(num_bins, 1000)
        self.assertEqual(len(headers), 3)

    def test_load_fail(self):
        filters = Filters(
                      peak_property = PeakProperty(1.2),
                      time_filters = TimeFilters(
                          keep_filters = [Filter('unit', 1, 2),
                                          Filter('test', 3, 4)],
                          remove_filters=[Filter('more', 5, 6),
                                          Filter('tests', 7, 8)]
                      )
                  )
        with self.assertRaises(RuntimeError):
            _ = self.presenter.load(filters)

    def test_update_N_events_success(self):
        for col_id in ['Start_time-table',
                       'End_time-table',
                       'filter_log-table',
                       'y0_log-table',
                       'yN_log-table',]:
            result = self.presenter.update_N_events(
                    [{'colId': col_id}], 'old'
                    )
            self.assertEqual(result, 'Number of events: Not Calculated')

    def test_update_N_events_fail(self):
        result = self.presenter.update_N_events([{'colId': 'unit test'}],
                                                'old')
        self.assertEqual(result, 'old')


if __name__ == '__main__':
    unittest.main()
