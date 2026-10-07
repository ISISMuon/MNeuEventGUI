import os
import sys
import unittest
from unittest import mock

import numpy as np
from MNeuEventLib import BatchData

from MNeuEventGUI.filters.presenter import FilterPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from data_paths import FILE  # noqa: E402

TT = '_time-table'
LT = '_log-table'


def load_data():
    """
    Load the test data file.
    :returns: a BatchData object with a single filter set
    """
    return BatchData(FILE, 64, 1)


class FilterPresenterTest(TestHelper):

    def setUp(self):
        self.presenter = FilterPresenter()

    def set_file_data(self):
        """
        Set up the presenter as if a filter file
        had been loaded. Uses fake values for the
        tables (should be dicts, but just checks they match)
        """
        self.presenter._time_file_data = 'time'
        self.presenter._log_file_data = 'log'
        self.presenter._amp_file_data = 2
        data = load_data()
        data.set_histogram_settings(0, 0., 1., 2)
        self.presenter._data = data

    def test_show_file_match(self):
        self.set_file_data()
        self.assertFalse(self.presenter.show_file('test.json', 'time', 'log',
                                                  2, 0., 1., 2))

    def test_show_file_match_amp_fails(self):
        self.set_file_data()
        self.assertTrue(self.presenter.show_file('test.json', 'time', 'log',
                                                 4, 0., 1., 2))

    def test_show_file_time_match(self):
        self.set_file_data()
        self.assertTrue(self.presenter.show_file('test.json', 'time', 'new',
                                                 2, 0., 1., 2))

    def test_show_file_log_match(self):
        self.set_file_data()
        self.assertTrue(self.presenter.show_file('test.json', 'new', 'log',
                                                 2, 0., 1., 2.))

    def test_show_file_hist_fails(self):
        """
        Test that histogram settings changing causes a non-match.
        """
        self.set_file_data()
        for hist_settings in [
            (1., 1., 2),
            (0., 2., 2),
            (0., 1., 5),
            ]:
            self.assertTrue(
                self.presenter.show_file('test.json', 'time', 'log', 2,
                                         *hist_settings)
                )

    def test_show_file_no_match(self):
        self.set_file_data()
        self.assertTrue(self.presenter.show_file('test.json', 'unit', 'test',
                                                 3, 5., 6.5, 7))

    def test_headers(self):
        self.assertEqual(len(self.presenter.headers), 3)

    def test_set_data(self):
        data = mock.Mock()
        # frame times are in ns
        data.dataset.get_frame_times.return_value = np.array([1e9, 2e9, 6e9])

        self.presenter._time.set_time_range = mock.Mock()

        self.presenter.set_data(data)
        self.presenter._time.set_time_range.assert_called_once()
        start, end = self.presenter._time.set_time_range.call_args[0]
        self.assertAlmostEqual(start, 1)
        self.assertAlmostEqual(end, 6 + 32e-6)
        self.assertEqual(self.presenter._data, data)
        self.assertEqual(self.presenter._time.data, data)
        self.assertEqual(self.presenter._log.data, data)

    def test_get_log_y_range_between(self):
        log = {'magic': 'between',
               'sample' + LT: 'Temp',
               'y0' + LT: 36,
               'yN' + LT: 37,
               'y_min' + LT: 35,
               'y_max' + LT: 39}

        self.presenter.set_data(load_data())
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

        self.presenter.set_data(load_data())
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

        self.presenter.set_data(load_data())
        low, high = self.presenter.get_log_y_range(log)
        self.assertEqual(low, 36)
        self.assertEqual(high, 39)

    def test_calculate_no_filters(self):
        self.presenter._data = load_data()
        N_str, err_msg = self.presenter.calculate(1)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 64,147')

    def test_calculate_amp_filter(self):
        data = load_data()
        data.set_amps_baseline(0, 2500.)
        self.presenter._data = data
        N_str, err_msg = self.presenter.calculate(1)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 7,944')

    def test_calculate_with_exclude_filter(self):
        data = load_data()
        data.set_time_type(0, 'exclude')
        data.add_time_filter(0, 'unit', 0.1, 1.2)
        self.presenter._data = data
        N_str, err_msg = self.presenter.calculate(1)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 57,653')

    def test_calculate_with_include_filter(self):
        data = load_data()
        data.set_time_type(0, 'include')
        data.add_time_filter(0, 'unit', 0.1, 1.2)
        self.presenter._data = data
        N_str, err_msg = self.presenter.calculate(1)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 6,494')

    def test_calculate_with_log_filter(self):
        data = load_data()
        data.add_log_filter_above(0, 'log', 'Temp', 35.5)
        self.presenter._data = data
        N_str, err_msg = self.presenter.calculate(1)
        self.assertEqual(err_msg, '')
        self.assertEqual(N_str.children,
                         'Number of events: 58,972')

    def test_calculate_with_error(self):
        data = mock.Mock()
        data.calculate.side_effect = RuntimeError("mock throw")
        self.presenter._data = data
        N_str, err_msg = self.presenter.calculate(1)
        self.assertEqual(err_msg, 'mock throw')
        self.assertEqual(N_str.children,
                         'Number of events: 0')

    def test_load_include(self):
        data = load_data()
        data.set_time_type(0, 'include')
        data.add_time_filter(0, 'unit', 1., 2.)
        data.add_time_filter(0, 'test', 3., 4.)
        data.add_log_filter(0, 'log_default_1', 'Temp', 36., 37.)
        data.set_amps_baseline(0, 1.2)
        self.presenter.set_data(data)

        (times, logs, amps,
         state, headers) = self.presenter.load(data._dict(0))
        self.assertEqual(state, 'Include')
        # the data does not preserve the order the filters were added
        self.assertCountEqual(times, [{'Name' + TT: 'unit',
                                     'Start' + TT: 1,
                                     'End' + TT: 2},
                                    {'Name' + TT: 'test',
                                     'Start' + TT: 3,
                                     'End' + TT: 4}])
        self.assertEqual(logs, [{'Name_log-table': 'log_default_1',
                                 'filter_log-table': 'between',
                                 'magic': 'between',
                                 'sample_log-table': 'Temp',
                                 'y0_log-table': 36,
                                 'yN_log-table': 37,
                                 'y_max_log-table': 39.0,
                                 'y_min_log-table': 35.0}
                                ])
        self.assertEqual(amps, 1.2)
        self.assertEqual(len(headers), 3)
        self.assertEqual(headers[2]['headerName'], 'Include Filter details')

    def test_load_exclude(self):
        data = load_data()
        data.set_time_type(0, 'exclude')
        data.add_time_filter(0, 'more', 5., 6.)
        data.add_time_filter(0, 'tests', 7., 8.)
        data.set_amps_baseline(0, 1.2)
        self.presenter.set_data(data)

        (times, logs, amps,
         state, headers) = self.presenter.load(data._dict(0))
        self.assertEqual(state, 'Exclude')
        # the data does not preserve the order the filters were added
        self.assertCountEqual(times, [{'Name' + TT: 'more',
                                     'Start' + TT: 5,
                                     'End' + TT: 6},
                                    {'Name' + TT: 'tests',
                                     'Start' + TT: 7,
                                     'End' + TT: 8}])
        self.assertEqual(logs, [])
        self.assertEqual(amps, 1.2)
        self.assertEqual(len(headers), 3)
        self.assertEqual(headers[2]['headerName'], 'Exclude Filter details')

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
