import unittest
from unittest import mock
from MuonDataLib.GUI.control_pane.presenter import ControlPanePresenter
from MuonDataLib.test_helpers.unit_test import TestHelper
from MuonDataLib.data.loader.load_events import load_events
import sys
import os
from dash import no_update
import numpy as np

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
                            '..',
                            'data_files',
                            'HIFI00195790.nxs')
        self.data = load_events(file, 64)
        # add some extra sample logs
        x, _ = self.data._get_sample_log('Temp').get_values()
        self.data.add_sample_log('B', x, np.cos(.2*x))
        self.data.add_sample_log('I', x, np.exp(-0.2*x))

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

        self.presenter.make_plot([], self.log_table, 0, 'Exclude')

    @property
    def get_fig(self):
        return self.presenter._plot.fig

    @property
    def logs(self):
        return self.data._dict['logs']

    def test_clear(self):
        self.presenter._filter._log._logs = 'logs'
        self.presenter._filter._data = 'data'

        self.presenter.clear()
        self.assertEqual(self.presenter._filter._log._logs, None)
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
        mock_logs = mock.Mock()
        self.presenter._filter._log._logs = mock_logs

        self.presenter.plot_default()
        self.presenter._plot.new_plot.assert_called_once_with(['I'],
                                                              mock_logs)

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
        self.presenter.add_filters = mock.Mock()
        """
        These mock return values are not realistic,
        but we just need to check they get passed correctly
        """
        self.presenter._filter.update_filters = mock.Mock()
        self.presenter.clear()

        self.presenter.make_plot([], [], 0, 'Exclude')
        self.presenter.add_filters.assert_not_called()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_make_plot_empty_filters(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filters = mock.Mock()
        """
        These mock return values are not realistic,
        but we just need to check they get passed correctly
        """
        self.presenter._filter.update_filters = mock.Mock(return_value=([],
                                                                        [],
                                                                        ''))
        self.presenter.make_plot([], [], 0, 'Exclude')

        self.presenter._plot.new_plot.assert_called_once_with(['Temp'],
                                                              self.logs)
        self.presenter.add_filters.assert_called_once_with([], [], [])

    def test_make_plot_one_log(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filters = mock.Mock()
        """
        These mock return values are not realistic,
        but we just need to check they get passed correctly
        """
        mock_update_filters = mock.Mock(return_value=([],
                                                      'log',
                                                      ''))
        self.presenter._filter.update_filters = mock_update_filters

        self.presenter.make_plot([], [self.log_table[0]], 0, 'Exclude')

        self.presenter._plot.new_plot.assert_called_once_with(['Temp'],
                                                              self.logs)

        mock_update_filters.assert_called_once_with([],
                                                    'Exclude',
                                                    [self.log_table[0]],
                                                    0)
        self.presenter.add_filters.assert_called_once_with([],
                                                           'log',
                                                           [self.log_table[0]])

    def test_make_plot_two_logs(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filters = mock.Mock()
        """
        These mock return values are not realistic,
        but we just need to check they get passed correctly
        """
        mock_update_filters = mock.Mock(return_value=([], 'log', ''))

        self.presenter._filter.update_filters = mock_update_filters

        self.presenter.make_plot([], self.log_table, 0, 'Exclude')

        self.presenter._plot.new_plot.assert_called_once_with(['Temp', 'B'],
                                                              self.logs)
        self.presenter.add_filters.assert_called_once_with([],
                                                           'log',
                                                           self.log_table)
        mock_update_filters.assert_called_once_with([],
                                                    'Exclude',
                                                    self.log_table,
                                                    0)

    def test_make_plot_two_logs_and_time(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filters = mock.Mock()
        """
        These mock return values are not realistic,
        but we just need to check they get passed correctly
        """
        mock_update_filters = mock.Mock(return_value=('time', 'log', ''))
        self.presenter._filter.update_filters = mock_update_filters

        time_data = [{'Name' + TT: 'time_Filter',
                      'Start' + TT: 1,
                      'End' + TT: 4}]

        self.presenter.make_plot(time_data,
                                 self.log_table,
                                 0,
                                 'Exclude')

        self.presenter._plot.new_plot.assert_called_once_with(['Temp', 'B'],
                                                              self.logs)

        mock_update_filters.assert_called_once_with(time_data,
                                                    'Exclude',
                                                    self.log_table,
                                                    0)
        self.presenter.add_filters.assert_called_once_with('time', 'log',
                                                           self.log_table)

    def test_add_filter_include(self):
        """
        by default includes log data
        """
        self.check_shapes(*DEFAULT_SHAPES)

        self.presenter.add_time_filters([{'Name' + TT: 'unit',
                                          'Start' + TT: 0.2,
                                          'End' + TT: 0.4},
                                         {'Name' + TT: 'test',
                                          'Start' + TT: 0.7,
                                          'End' + TT: 0.8}],
                                        'Include')

        self.check_shapes([],
                          [[0.2, 0.4, 0, 1, 'y'],
                           [0.2, 0.4, 0, 1, 'y2'],
                           [0.7, 0.8, 0, 1, 'y'],
                           [0.7, 0.8, 0, 1, 'y2']])

    def test_add_filter_exclude(self):
        # by default should have 2 shapes that cover both plots
        self.check_shapes(*DEFAULT_SHAPES)

        self.presenter.add_time_filters([{'Name' + TT: 'unit',
                                          'Start' + TT: 0.2,
                                          'End' + TT: 0.4},
                                         {'Name' + TT: 'test',
                                          'Start' + TT: 0.7,
                                          'End' + TT: 0.8}],
                                        'Exclude')
        self.check_shapes([],
                          [[0., 0.2, 0, 1, 'y'],
                           [0., 0.2, 0, 1, 'y2'],
                           [0.4, 0.7, 0, 1, 'y'],
                           [0.4, 0.7, 0, 1, 'y2'],
                           [0.8, 4., 0, 1, 'y'],
                           [0.8, 4., 0, 1, 'y2']])

    def test_add_filter_include_empty(self):
        # by default should have 2 shapes that cover both plots
        self.check_shapes(*DEFAULT_SHAPES)

        self.presenter.add_time_filters([], 'Include')

        self.check_shapes([], [])

    def test_add_filter_exclude_empty(self):
        # by default should have 2 shapes that cover both plots
        self.check_shapes(*DEFAULT_SHAPES)

        self.presenter.add_time_filters([],
                                        'Exclude')

        self.check_shapes([],
                          [[0, 4, 0, 1, 'x'],
                           [0, 4, 0, 1, 'x1']])

    def test_apply_exc_data_empty(self):
        shade = mock.Mock()
        self.presenter._plot.add_shaded_region = shade
        self.presenter.apply_exc_data([], [])
        self.assertEqual(shade.call_count,
                         0)

    def test_apply_exc_data_one(self):
        shade = mock.Mock()
        self.presenter._plot.add_shaded_region = shade
        self.presenter.apply_exc_data([.1], [.3])
        self.assertEqual(shade.call_count,
                         2)
        shade.assert_any_call(0, .1)
        shade.assert_any_call(0.3, 4.)

    def test_apply_exc_data_multiple(self):
        shade = mock.Mock()
        self.presenter._plot.add_shaded_region = shade
        self.presenter.apply_exc_data([.1, .3], [.2, .4])
        self.assertEqual(shade.call_count,
                         3)
        shade.assert_any_call(0, .1)
        shade.assert_any_call(0.2, .3)
        shade.assert_any_call(0.4, 4.)

    def test_set_data(self):
        reset = mock.Mock()
        self.presenter._plot.reset_plot_range = reset
        data = mock.Mock()
        data.get_frame_start_times = mock.Mock(return_value=[0.1, 3, 6, 11])
        data._dict = {'logs': 'log data'}

        self.presenter.set_data(data)

        self.assertEqual(reset.call_count, 1)
        self.assertEqual(self.presenter._filter._data,
                         data)
        self.assertEqual(self.presenter._filter._log._logs,
                         'log data')

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
        (data, log_data, amp, min_time,
         max_time, num_bins, state, cols) = self.presenter.read_filter(FILTER)
        self.assertEqual(state, 'Include')
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], {'Name' + TT: 'first',
                                   'Start' + TT: 0.01,
                                   'End' + TT: 0.02})
        self.assertEqual(data[1], {'Name' + TT: 'second',
                                   'Start' + TT: 0.05,
                                   'End' + TT: 0.06})
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
        self.assertEqual(min_time, 0.5)
        self.assertEqual(max_time, 15.22)
        self.assertEqual(num_bins, 1024)
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
        self.assertEqual(func.call_count, 5)
        # reverse order
        expect = [[0, .1],
                  [.2, .3],
                  [.4, .5],
                  [.6, .7],
                  [.8, 4]]
        for k in range(len(expect)):
            self.assertEqual(len(args[k][0]), 3)
            self.assertEqual(expect[k][0], args[k][0][0])
            self.assertEqual(expect[k][1], args[k][0][1])
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

    def test_add_filters_none(self):
        self.presenter.wrap_add_rect = mock.Mock()
        self.presenter.wrap_add_shaded_region = mock.Mock()

        self.presenter.add_filters([], [], [])
        self.presenter.wrap_add_rect.assert_not_called()
        self.presenter.wrap_add_shaded_region.assert_called_once_with(0., 4.)

    def test_add_filters_time(self):
        self.presenter.wrap_add_rect = mock.Mock()
        self.presenter.wrap_add_shaded_region = mock.Mock()
        self.presenter.add_filters([1], [2], [])
        self.presenter.wrap_add_rect.assert_not_called()

        args = self.presenter.wrap_add_shaded_region.call_args_list
        self.assertEqual(len(args), 2)
        # reverse order
        expect = [[0, 1],
                  [2, 4]]
        for k in range(len(expect)):
            self.assertEqual(len(args[k][0]), 2)
            self.assertEqual(expect[k][0], args[k][0][0])
            self.assertEqual(expect[k][1], args[k][0][1])

    def test_add_filters_log(self):
        self.presenter.wrap_add_rect = mock.Mock()
        self.presenter.wrap_add_shaded_region = mock.Mock()

        self.presenter.add_filters([1], [2],
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

        args = self.presenter.wrap_add_rect.call_args_list
        self.assertEqual(len(args), 2)
        expect = [[0, 1, 0.9, 1., ''],
                  [2, 4, 0.9, 1., '']]
        for k in range(len(expect)):
            self.assertEqual(len(args[k][0]), 5)
            self.assertEqual(expect[k][0], args[k][0][0])
            self.assertEqual(expect[k][1], args[k][0][1])
            self.assertEqual(expect[k][2], args[k][0][2])
            self.assertEqual(expect[k][3], args[k][0][3])
            self.assertEqual(expect[k][4], args[k][0][4])


if __name__ == '__main__':
    unittest.main()
