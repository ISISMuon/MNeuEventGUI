import os
import sys
import unittest
from unittest import mock

import numpy as np
from dash import no_update
from MNeuEventLib import BatchData

from MNeuEventGUI.control_pane.presenter import ControlPanePresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from MNeuEventGUI.utils.batch import NUM_BATCHES, batch_colour, tab_id

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE  # noqa: E402

TT = '_time-table'
LT = '_log-table'


def empty_tables():
    """
    :returns: an empty table for each batch
    """
    return [[] for _ in range(NUM_BATCHES)]


def tables(**batches):
    """
    Gets a table for each batch, with
    the given tables for some of the batches.
    :param batches: the tables keyed by 'b' + batch index
    :returns: a table for each batch
    """
    data = empty_tables()
    for key, table in batches.items():
        data[int(key[1:])] = table
    return data


def log_row(name, log, f_type, y0, yN):
    return {'Name' + LT: name,
            'sample' + LT: log,
            'filter' + LT: f_type,
            'y0' + LT: y0,
            'yN' + LT: yN,
            'magic': f_type,
            'y_min' + LT: 0.,
            'y_max' + LT: 1.}


TEMP_ROW = log_row('log_temp', 'Temp', 'between', 0.2, 0.8)
B_ROW = log_row('log_B', 'B', 'above', 0.6, 1.)


class ControlPanePresenterTest(TestHelper):

    def setUp(self):
        self.data = BatchData(FILE, 64, NUM_BATCHES)

        self.presenter = ControlPanePresenter()
        self.presenter.set_data(self.data)

        self.presenter.make_plot(empty_tables(),
                                 tables(b0=[TEMP_ROW, B_ROW]),
                                 [False] * NUM_BATCHES,
                                 tab_id(0))

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

    def shading_calls(self):
        """
        :returns: the arguments for each call to
        add_filter_shading
        """
        return [call[0] for call in
                self.presenter.add_filter_shading.call_args_list]

    def test_filters(self):
        self.assertEqual(len(self.presenter._filters), NUM_BATCHES)
        for k, filter_presenter in enumerate(self.presenter._filters):
            self.assertEqual(filter_presenter.batch, k)

    def test_clear(self):
        self.presenter.clear()
        self.assertEqual(self.presenter._data, None)
        for filter_presenter in self.presenter._filters:
            self.assertEqual(filter_presenter._data, None)
            self.assertEqual(filter_presenter._log.data, None)

    def test_empty(self):
        self.presenter._plot.plot = mock.Mock()
        self.presenter.empty()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_plot_default(self):
        self.presenter._filters[0]._log.get_new_log_name = mock.Mock()
        self.presenter._filters[0]._log.get_new_log_name.return_value = 'I'
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

    def test_plot_log_names_default(self):
        self.assertEqual(self.presenter.plot_log_names(empty_tables()),
                         ['Temp'])

    def test_plot_log_names_union(self):
        # ordered by first appearance, with no repeats
        names = self.presenter.plot_log_names(
            tables(b0=[B_ROW],
                   b1=[TEMP_ROW, B_ROW],
                   b2=[log_row('a', 'I', 'between', 0, 1)]))
        self.assertEqual(names, ['B', 'Temp', 'I'])

    def test_make_plot_empty_data(self):
        self.presenter._plot.plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()
        self.presenter.clear()

        self.presenter.make_plot(empty_tables(), empty_tables(),
                                 [False] * NUM_BATCHES, tab_id(0))
        self.presenter.add_filter_shading.assert_not_called()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_make_plot_empty_filters(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        self.presenter.make_plot(empty_tables(), empty_tables(),
                                 [False] * NUM_BATCHES, tab_id(0))

        self.assert_new_plot(['Temp'])
        # every batch keeps all of the data
        calls = self.shading_calls()
        self.assertEqual(len(calls), NUM_BATCHES)
        for batch, start, stop, log_data, names, outline in calls:
            self.assertEqual(start, [])
            self.assertEqual(stop, [])
            self.assertEqual(log_data, [])
            self.assertEqual(names, ['Temp'])
            self.assertEqual(outline, batch == 0)

    def test_make_plot_active_batch_last(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        self.presenter.make_plot(empty_tables(), empty_tables(),
                                 [False] * NUM_BATCHES, tab_id(1))

        calls = self.shading_calls()
        self.assertEqual([call[0] for call in calls], [0, 2, 1])
        # only the active batch has an outline
        self.assertEqual([call[5] for call in calls],
                         [False, False, True])

    def test_make_plot_logs_from_all_batches(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()
        log_data = tables(b0=[TEMP_ROW], b2=[B_ROW])

        self.presenter.make_plot(empty_tables(), log_data,
                                 [False] * NUM_BATCHES, tab_id(0))

        self.assert_new_plot(['Temp', 'B'])
        # each batch gets its own log table
        for batch, _, _, logs, names, _ in self.shading_calls():
            self.assertEqual(logs, log_data[batch])
            self.assertEqual(names, ['Temp', 'B'])

    def test_make_plot_time_filter(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        time_data = tables(b1=[{'Name' + TT: 'time_Filter',
                                'Start' + TT: 1,
                                'End' + TT: 4}])
        # the filter times come from the data, not the table
        self.data.add_time_filter(1, 'time_Filter', 1., 4.)

        self.presenter.make_plot(time_data, empty_tables(),
                                 [False] * NUM_BATCHES, tab_id(0))

        calls = {call[0]: call for call in self.shading_calls()}
        # filter times are converted from ns to seconds
        self.assertArrays(calls[1][1], [1.])
        self.assertArrays(calls[1][2], [4.])
        # the other batches are unfiltered
        self.assertEqual(calls[0][1], [])
        self.assertEqual(calls[2][1], [])

    def test_set_data(self):
        reset = mock.Mock()
        self.presenter._plot.reset_plot_range = reset
        data = mock.Mock()
        data.dataset.get_frame_times = mock.Mock(
            return_value=np.array([0.1, 3, 6, 11]))

        self.presenter.set_data(data)

        self.assertEqual(reset.call_count, 1)
        self.assertEqual(self.presenter._data, data)
        for filter_presenter in self.presenter._filters:
            self.assertEqual(filter_presenter._data, data)

    def test_headers(self):
        headers = self.presenter.headers
        self.assertEqual(len(headers), NUM_BATCHES)
        # just check the number of header groups
        for header in headers:
            self.assertEqual(len(header), 3)

    def test_calculate(self):
        self.data.set_amps_baseline(1, 2500.)
        N_strs, err_msg = self.presenter.calculate([1, None, None])
        self.assertEqual(err_msg, '')
        self.assertEqual([N.children for N in N_strs],
                         ['Number of events: 64,147',
                          'Number of events: 7,944',
                          'Number of events: 64,147'])

    def test_calculate_with_error(self):
        data = mock.Mock()
        data.calculate.side_effect = RuntimeError("mock throw")
        self.presenter._data = data
        N_strs, err_msg = self.presenter.calculate([1, None, None])
        self.assertEqual(err_msg, 'mock throw')
        self.assertEqual([N.children for N in N_strs],
                         ['Number of events: 0'] * NUM_BATCHES)

    def test_refresh(self):
        self.data.set_time_type(1, 'exclude')
        self.data.add_time_filter(1, 'first', 0.01, 0.02)
        self.data.set_amps_baseline(1, 2.7)
        self.data.set_histogram_settings(1, 0.5, 15.22, 1024)

        values = self.presenter.refresh()
        self.assertEqual(len(values), NUM_BATCHES)

        (data, log_data, amp, state,
         min_time, max_time,
         num_bins, cols) = values[1]

        self.assertEqual(data, [{'Name' + TT: 'first',
                                 'Start' + TT: 0.01,
                                 'End' + TT: 0.02}])
        self.assertEqual(log_data, [])
        self.assertEqual(amp, 2.7)
        self.assertEqual(state, 'Exclude')
        self.assertEqual(min_time, 0.5)
        self.assertEqual(max_time, 15.22)
        self.assertEqual(num_bins, 1024)
        self.assertEqual(cols[2]['headerName'], 'Exclude Filter details')

        # the other batches are unchanged
        self.assertEqual(values[0][0], [])
        self.assertEqual(values[0][3], 'Include')


class AddFilterShadingTest(TestHelper):
    """
    Tests for the shaded regions of a single batch.
    """

    def setUp(self):
        self.data = BatchData(FILE, 64, NUM_BATCHES)
        self.presenter = ControlPanePresenter()
        self.presenter.set_data(self.data)
        self.plot = mock.Mock()
        self.plot._min = 0.
        self.plot._max = 4.
        self.presenter._plot = self.plot

    def test_none(self):
        self.presenter.add_filter_shading(1, [], [], [], ['Temp'], True)
        self.plot.add_shaded_region.assert_called_once_with(
            0., 4., batch_colour(1), True)
        self.plot.add_rect.assert_not_called()
        self.plot.add_band.assert_not_called()

    def test_time(self):
        self.presenter.add_filter_shading(2, [1, 3], [2, 4], [],
                                          ['Temp'], False)
        self.assertEqual(self.plot.add_shaded_region.call_args_list,
                         [mock.call(1, 2, batch_colour(2), False),
                          mock.call(3, 4, batch_colour(2), False)])
        self.plot.add_rect.assert_not_called()

    def test_log(self):
        self.presenter.add_filter_shading(0, [1], [2], [B_ROW],
                                          ['B'], True)
        self.plot.add_shaded_region.assert_not_called()
        self.plot.add_band.assert_not_called()
        self.plot.add_rect.assert_called_once_with(
            1, 0.6, 2, 1., '', batch_colour(0), True)
        self.assertEqual(self.plot.add_hline.call_args_list,
                         [mock.call(0.6, row=1, colour=batch_colour(0)),
                          mock.call(1., row=1, colour=batch_colour(0))])

    def test_log_on_second_subplot(self):
        # the batch only filters on the second sample log,
        # so the first is shaded for the full height
        self.presenter.add_filter_shading(1, [1], [2], [B_ROW],
                                          ['Temp', 'B'], False)
        self.plot.add_band.assert_called_once_with(
            1, 2, '', batch_colour(1), False)
        self.plot.add_rect.assert_called_once_with(
            1, 0.6, 2, 1., '2', batch_colour(1), False)
        self.assertEqual(self.plot.add_hline.call_args_list,
                         [mock.call(0.6, row=2, colour=batch_colour(1)),
                          mock.call(1., row=2, colour=batch_colour(1))])


class DisplayHoverTest(TestHelper):

    def setUp(self):
        self.presenter = ControlPanePresenter()
        self.hover = {'points': [{'bbox': [1, 2, 3, 4],
                                  'x': 0.5,
                                  'y': 0.5}]}

    def check_hover_text(self, hover, x, status):
        """
        Check the tooltip text.
        :param hover: the tooltip
        :param x: the expected x value
        :param status: the expected status line for each batch
        """
        expect = ['Data Point',
                  f'x: {x:.3f},  y: 0.500',
                  'Status',
                  *status]
        self.assertEqual([child.children for child in hover.children],
                         expect)

    def hover_at(self, x):
        self.hover['points'][0]['x'] = x
        return self.hover

    def test_none(self):
        result = self.presenter.display_hover(None,
                                              empty_tables(),
                                              ['Include'] * NUM_BATCHES)
        self.assertEqual(result, (False, no_update, no_update))

    def test_no_filters(self):
        result = self.presenter.display_hover(
            self.hover,
            empty_tables(),
            ['Include', 'Exclude', 'Include'])
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])
        self.check_hover_text(result[2], 0.5,
                              ['Batch 0: Keep data: False',
                               'Batch 1: Keep data: True',
                               'Batch 2: Keep data: False'])

    def test_filters_per_batch(self):
        unit = {'Name' + TT: 'unit',
                'Start' + TT: 0.4,
                'End' + TT: 0.6}
        test = {'Name' + TT: 'test',
                'Start' + TT: 0.2,
                'End' + TT: 0.7}
        result = self.presenter.display_hover(
            self.hover,
            tables(b0=[unit, test], b1=[test], b2=[unit]),
            ['Include', 'Exclude', 'Exclude'])
        self.check_hover_text(result[2], 0.5,
                              ['Batch 0: Keep data: True. '
                               'Added by: unit, test, ',
                               'Batch 1: Keep data: False. '
                               'Removed by: test, ',
                               'Batch 2: Keep data: False. '
                               'Removed by: unit, '])

    def test_not_over_filters(self):
        unit = {'Name' + TT: 'unit',
                'Start' + TT: 0.4,
                'End' + TT: 0.6}
        result = self.presenter.display_hover(
            self.hover_at(0.2),
            tables(b0=[unit], b1=[unit]),
            ['Include', 'Exclude', 'Include'])
        self.check_hover_text(result[2], 0.2,
                              ['Batch 0: Keep data: False',
                               'Batch 1: Keep data: True',
                               'Batch 2: Keep data: False'])


if __name__ == '__main__':
    unittest.main()
