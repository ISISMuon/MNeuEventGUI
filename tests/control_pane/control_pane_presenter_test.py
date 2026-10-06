import unittest
from unittest import mock
import sys
import os

from MNeuEventGUI.control_pane.presenter import ControlPanePresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper

import numpy as np
from dash import no_update
from MNeuEventLib import BatchData

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILTER  # noqa: E402


TT = '_time-table'
LT = '_log-table'

DEFAULT_SHAPES = ([],
                  [[0, 4, 0.0, 1., 'y'],
                   [0, 4, 0.0, 1., 'y2'],
                   ])


class ControlPanePresenterTest(TestHelper):

    def setUp(self):
        file = os.path.join(os.path.dirname(__file__),
                            '..',
                            'data_files',
                            'HIFI00195790.nxs')
        self.data = BatchData(file, 64, 1)

        self.presenter = ControlPanePresenter()
        self.presenter.set_data(self.data)

        self.log_table = [{'Delete' + LT: '',
                           'Name' + LT: 'log_temp',
                           'sample' + LT: 'Temp',
                           'filter' + LT: 'between',
                           'y0' + LT: 0.9,
                           'yN' + LT: 0.8,
                           'magic': 'between',
                           'y_min' + LT: 0.7,
                           'y_max' + LT: 1},
                          {'Delete' + LT: '',
                           'Name_' + LT: 'log_B',
                           'sample' + LT: 'B',
                           'filter' + LT: 'above',
                           'y0' + LT: 0.6,
                           'yN' + LT: 0.8,
                           'magic': 'between',
                           'y_min' + LT: 0.4,
                           'y_max' + LT: 1}]

        self.presenter.make_plot([], self.log_table, 'Exclude', 0)

    @property
    def get_fig(self):
        return self.presenter._plot.fig

    def assert_new_plot(self, names):
        """
        Check that new_plot was called once with the
        named sample logs from the data.
        :param names: the expected sample log names
        """
        self.presenter._plot.new_plot.assert_called_once()
        plot_names, logs = self.presenter._plot.new_plot.call_args[0]
        self.assertEqual(plot_names, names)
        self.assertEqual(len(logs), len(names))
        for name, log in zip(names, logs):
            expected = self.data.dataset.get_sample_log(name)
            self.assertEqual(log['name'], name)
            self.assertArrays(log['time'], expected['time'])
            self.assertArrays(log['value'], expected['value'])

    def assert_shading(self, start, stop, log_data):
        """
        Check that add_filter_shading was called once
        with the expected filter times (in seconds).
        :param start: the expected start times
        :param stop: the expected stop times
        :param log_data: the expected log table data
        """
        self.presenter.add_filter_shading.assert_called_once()
        args = self.presenter.add_filter_shading.call_args[0]
        # assertArrays does not check lengths of empty arrays
        self.assertEqual(len(args[0]), len(start))
        self.assertEqual(len(args[1]), len(stop))
        self.assertArrays(args[0], start)
        self.assertArrays(args[1], stop)
        self.assertEqual(args[2], log_data)

    def test_clear(self):
        self.presenter._filter._log._data = 'logs'
        self.presenter._filter._data = 'data'

        self.presenter.clear()
        self.assertEqual(self.presenter._filter._log._data, None)
        self.assertEqual(self.presenter._filter._data, None)

    def test_empty(self):
        self.presenter._plot.plot = mock.Mock()
        self.presenter.empty()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_plot_default(self):
        self.presenter._filter._log.get_new_log_name = mock.Mock()
        self.presenter._filter._log.get_new_log_name.return_value = 'I'
        self.presenter._plot.new_plot = mock.Mock()

        self.presenter.plot_default()
        self.assert_new_plot(['I'])

    def test_plot_default_empty(self):
        self.presenter._plot.plot = mock.Mock()
        self.presenter.clear()

        self.presenter.plot_default()
        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_make_plot_empty_data(self):
        self.presenter._plot.plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()
        self.presenter.clear()

        self.presenter.make_plot([], [], 'Exclude', 0)
        self.presenter.add_filter_shading.assert_not_called()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_make_plot_empty_filters(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        self.presenter.make_plot([], [], 'Exclude', 0)

        # no default sample log in the file, so use the first one
        self.assert_new_plot(['B'])
        self.assert_shading([], [], [])

    def test_make_plot_one_log(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        self.presenter.make_plot([], [self.log_table[0]], 'Exclude', 0)

        self.assert_new_plot(['Temp'])
        self.assert_shading([], [], [self.log_table[0]])

    def test_make_plot_two_logs(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        self.presenter.make_plot([], self.log_table, 'Exclude', 0)

        self.assert_new_plot(['Temp', 'B'])
        self.assert_shading([], [], self.log_table)

    def test_make_plot_two_logs_and_time(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        time_data = [{'Name' + TT: 'time_Filter',
                      'Start' + TT: 1,
                      'End' + TT: 4}]
        # the filter times come from the data, not the table
        self.data.add_time_filter(0, 'time_Filter', 1., 4.)

        self.presenter.make_plot(time_data,
                                 self.log_table,
                                 'Exclude',
                                 0)

        self.assert_new_plot(['Temp', 'B'])
        # filter times are converted from ns to seconds
        self.assert_shading([1.], [4.], self.log_table)

    def test_set_data(self):
        reset = mock.Mock()
        self.presenter._plot.reset_plot_range = reset
        data = mock.Mock()
        data.dataset.get_frame_times = mock.Mock(
            return_value=np.array([0.1, 3, 6, 11]))

        self.presenter.set_data(data)

        self.assertEqual(reset.call_count, 1)
        self.assertEqual(self.presenter._filter._data,
                         data)

    def test_display_hover_None(self):
        result = self.presenter.display_hover(None,
                                              {},
                                              'Include')
        self.assertEqual(result[0], False)
        self.assertEqual(result[1], no_update)
        self.assertEqual(result[2], no_update)

    def test_headers(self):
        # just check the number of header groups
        self.assertEqual(len(self.presenter.headers), 3)

    def check_hover_text(self, hover, expect):

        # loop over html objects for the tooltip
        for k, child in enumerate(hover.children):
            self.assertEqual(child.children,
                             expect[k])

    def test_display_hover_include_not_over_shaded(self):
        hover = {}
        hover['points'] = [{'bbox': [1, 2, 3, 4],
                            'x': 0.2,
                            'y': 0.5}]
        filters = [{'Name' + TT: 'test',
                    'Start' + TT: 0.4,
                    'End' + TT: 0.6}]

        result = self.presenter.display_hover(hover,
                                              filters,
                                              'Include')
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])

        expect = ['Data Point',
                  'x: 0.200,  y: 0.500',
                  'Status',
                  'Keep data: False']
        self.check_hover_text(result[2], expect)

    def test_display_hover_include_over_shaded(self):
        hover = {}
        hover['points'] = [{'bbox': [1, 2, 3, 4],
                            'x': 0.5,
                            'y': 0.5}]
        filters = [{'Name' + TT: 'test',
                    'Start' + TT: 0.4,
                    'End' + TT: 0.6}]

        result = self.presenter.display_hover(hover,
                                              filters,
                                              'Include')
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])

        expect = ['Data Point',
                  'x: 0.500,  y: 0.500',
                  'Status',
                  'Keep data: True. Added by: test, ']
        self.check_hover_text(result[2], expect)

    def test_display_hover_include_over_shaded_2(self):
        hover = {}
        hover['points'] = [{'bbox': [1, 2, 3, 4],
                            'x': 0.5,
                            'y': 0.5}]
        filters = [{'Name' + TT: 'unit',
                    'Start' + TT: 0.4,
                    'End' + TT: 0.6},
                   {'Name' + TT: 'test',
                    'Start' + TT: 0.2,
                    'End' + TT: 0.7},
                   ]

        result = self.presenter.display_hover(hover,
                                              filters,
                                              'Include')
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])

        expect = ['Data Point',
                  'x: 0.500,  y: 0.500',
                  'Status',
                  'Keep data: True. Added by: unit, test, ']
        self.check_hover_text(result[2], expect)

    def test_display_hover_exclude_not_over_shaded(self):
        hover = {}
        hover['points'] = [{'bbox': [1, 2, 3, 4],
                            'x': 0.5,
                            'y': 0.5}]
        filters = [{'Name' + TT: 'test',
                    'Start' + TT: 0.4,
                    'End' + TT: 0.6}]

        result = self.presenter.display_hover(hover,
                                              filters,
                                              'Exclude')
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])

        expect = ['Data Point',
                  'x: 0.500,  y: 0.500',
                  'Status',
                  'Keep data: False. Removed by: test, ']
        self.check_hover_text(result[2], expect)

    def test_display_hover_exclude_over_shaded(self):
        hover = {}
        hover['points'] = [{'bbox': [1, 2, 3, 4],
                            'x': 0.2,
                            'y': 0.5}]
        filters = [{'Name' + TT: 'test',
                    'Start' + TT: 0.4,
                    'End' + TT: 0.6}]

        result = self.presenter.display_hover(hover,
                                              filters,
                                              'Exclude')
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])

        expect = ['Data Point',
                  'x: 0.200,  y: 0.500',
                  'Status',
                  'Keep data: True']
        self.check_hover_text(result[2], expect)

    def test_display_hover_exclude_not_over_shaded_2(self):
        hover = {}
        hover['points'] = [{'bbox': [1, 2, 3, 4],
                            'x': 0.5,
                            'y': 0.5}]
        filters = [{'Name' + TT: 'unit',
                    'Start' + TT: 0.4,
                    'End' + TT: 0.6},
                   {'Name' + TT: 'test',
                    'Start' + TT: 0.2,
                    'End' + TT: 0.7},
                   ]

        result = self.presenter.display_hover(hover,
                                              filters,
                                              'Exclude')
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])

        expect = ['Data Point',
                  'x: 0.500,  y: 0.500',
                  'Status',
                  'Keep data: False. Removed by: unit, test, ']
        self.check_hover_text(result[2], expect)

    def test_read_filter(self):
        (data, log_data, amp, state, cols) = self.presenter.read_filter(FILTER)
        self.assertEqual(state, 'Include')
        self.assertEqual(len(data), 2)
        self.assertContents(data, [{'Name' + TT: 'first',
                                   'Start' + TT: 0.01,
                                   'End' + TT: 0.02},
                                   {'Name' + TT: 'second',
                                   'Start' + TT: 0.05,
                                   'End' + TT: 0.06}])
        self.assertEqual(log_data,
                         [{'Name' + LT: 'log_default_1',
                           'sample' + LT: 'Temp',
                           'filter' + LT: 'between',
                           'y0' + LT: 0.0044,
                           'yN' + LT: 0.163,
                           'magic': 'between',
                           'y_min' + LT: 35.0,
                           'y_max' + LT: 39.0}])

        self.assertEqual(amp, 3.14)
        # this is the only bit that can change
        self.assertEqual(cols[2]['headerName'], 'Include Filter details')

    def test_loop_over_filters(self):
        func = mock.Mock()
        f_start = [.1, .3, .5, .7]
        f_end = [.2, .4, .6, .8]

        self.presenter._loop_over_filters(func,
                                          f_start,
                                          f_end,
                                          'not used')
        args = func.call_args_list
        self.assertEqual(func.call_count, 4)

        for k in range(len(f_start)):
            self.assertEqual(len(args[k][0]), 3)
            self.assertEqual(f_start[k], args[k][0][0])
            self.assertEqual(f_end[k], args[k][0][1])
            self.assertEqual('not used', args[k][0][2])

    def test_wrap_add_shaded_region(self):
        self.presenter._plot.add_shaded_region = mock.Mock()
        self.presenter.wrap_add_shaded_region(14, 79, 'not used')
        self.presenter._plot.add_shaded_region.assert_called_once_with(14,
                                                                       79)

    def test_wrap_add_rect(self):
        self.presenter._plot.add_rect = mock.Mock()
        self.presenter.wrap_add_rect(4, 6, 3, 8, 'x1')
        self.presenter._plot.add_rect.assert_called_once_with(4, 3, 6, 8, 'x1')

    def test_add_filter_shading_none(self):
        self.presenter.wrap_add_rect = mock.Mock()
        self.presenter.wrap_add_shaded_region = mock.Mock()

        self.presenter.add_filter_shading([], [], [])
        self.presenter.wrap_add_rect.assert_not_called()
        self.presenter.wrap_add_shaded_region.assert_called_once_with(0., 4.)

    def test_add_filter_shading_time(self):
        self.presenter.wrap_add_rect = mock.Mock()
        self.presenter.wrap_add_shaded_region = mock.Mock()
        self.presenter.add_filter_shading([1], [2], [])
        self.presenter.wrap_add_rect.assert_not_called()

        self.presenter.wrap_add_shaded_region.assert_called_once_with(1, 2)

    def test_add_filter_shading_log(self):
        self.presenter.wrap_add_rect = mock.Mock()
        self.presenter.wrap_add_shaded_region = mock.Mock()

        self.presenter.add_filter_shading([1], [2],
                                   [{'Delete' + LT: '',
                                     'Name_' + LT: 'log_B',
                                     'sample' + LT: 'B',
                                     'filter' + LT: 'above',
                                     'y0' + LT: 0.9,
                                     'yN' + LT: 1.,
                                     'magic': 'above',
                                     'y_min' + LT: 0.4,
                                     'y_max' + LT: 1}])

        self.presenter.wrap_add_shaded_region.assert_not_called()

        self.presenter.wrap_add_rect.assert_called_once_with(
            1,
            2,
            0.9,
            1,
            ''
                )

if __name__ == '__main__':
    unittest.main()
