import os
import sys
import unittest
from unittest import mock

import numpy as np
from dash import no_update
from MNeuEventLib import BatchData

from MNeuEventGUI.control_pane.presenter import ControlPanePresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from MNeuEventGUI.utils.batch import batch_colour
from MNeuEventGUI.utils.errors import GUIError

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE  # noqa: E402

# the tests use several batches
NUM_BATCHES = 3

TT = '_time-table'
LT = '_log-table'


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

        self.presenter = ControlPanePresenter(NUM_BATCHES)
        self.presenter.set_data(self.data)

    def make_plot(self, active=0):
        """
        Make the plot, as the callback would.
        :param active: the index of the active batch
        """
        self.presenter.make_plot([], [], False, active)

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

    def mock_plot(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

    def test_make_plot_with_real_plot(self):
        self.data.add_log_filter(0, 'log_temp', 'Temp', 36., 37.)
        self.data.add_time_filter(1, 'first', 1., 4.)
        self.make_plot()

    def test_clear(self):
        self.presenter.clear()
        self.assertEqual(self.presenter._data, None)
        filters = self.presenter._filters
        self.assertEqual(filters._data, None)
        self.assertEqual(filters._time.data, None)
        self.assertEqual(filters._log.data, None)
        self.assertEqual(filters._amp.data, None)
        self.assertEqual(filters._hist_settings.data, None)

    def test_empty(self):
        self.presenter._plot.plot = mock.Mock()
        self.presenter.empty()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_plot_default(self):
        self.presenter._filters._log.get_new_log_name = mock.Mock()
        self.presenter._filters._log.get_new_log_name.return_value = 'I'
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
        self.assertEqual(self.presenter.plot_log_names([[], [], []]),
                         ['Temp'])

    def test_plot_log_names_union(self):
        # ordered by first appearance, with no repeats
        names = self.presenter.plot_log_names(
            [[B_ROW], [TEMP_ROW, B_ROW],
             [log_row('a', 'I', 'between', 0, 1)]])
        self.assertEqual(names, ['B', 'Temp', 'I'])

    def test_make_plot_empty_data(self):
        self.presenter._plot.plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()
        self.presenter.clear()

        self.make_plot()
        self.presenter.add_filter_shading.assert_not_called()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_make_plot_empty_filters(self):
        self.mock_plot()
        self.make_plot()

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
        self.mock_plot()
        self.make_plot(1)

        calls = self.shading_calls()
        self.assertEqual([call[0] for call in calls], [0, 2, 1])
        # only the active batch has an outline
        self.assertEqual([call[5] for call in calls],
                         [False, False, True])

    def test_make_plot_logs_from_all_batches(self):
        self.mock_plot()
        # the filters are read from the data, for every batch
        self.data.add_log_filter(0, 'log_temp', 'Temp', 36., 37.)
        self.data.add_log_filter(2, 'log_B', 'B', 0.7, 0.9)

        self.make_plot()

        self.assert_new_plot(['Temp', 'B'])
        # each batch gets its own log filters
        logs = {batch: [row['Name' + LT] for row in rows]
                for batch, _, _, rows, _, _ in self.shading_calls()}
        self.assertEqual(logs, {0: ['log_temp'], 1: [], 2: ['log_B']})

    def test_make_plot_time_filter(self):
        self.mock_plot()
        self.data.add_time_filter(1, 'time_Filter', 1., 4.)

        self.make_plot()

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
        self.assertEqual(self.presenter._filters._data, data)

    def test_headers(self):
        # just check the number of header groups
        self.assertEqual(len(self.presenter.headers), 3)

    def test_refresh(self):
        self.data.set_time_type(1, 'exclude')
        self.data.add_time_filter(1, 'first', 0.01, 0.02)
        self.data.set_amps_baseline(1, 2.7)
        self.data.set_histogram_settings(1, 0.5, 15.22, 1024)

        (data, log_data, amp, state,
         min_time, max_time,
         num_bins, cols) = self.presenter.refresh(1)

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
        values = self.presenter.refresh(0)
        self.assertEqual(values[0], [])
        self.assertEqual(values[3], 'Include')


class BatchControlsTest(TestHelper):
    """
    Tests for choosing, adding and removing batches.
    """

    def setUp(self):
        self.data = BatchData(FILE, 64, NUM_BATCHES)
        self.presenter = ControlPanePresenter(NUM_BATCHES)
        self.presenter.set_data(self.data)

    def test_initial_batches(self):
        presenter = ControlPanePresenter()
        self.assertEqual(presenter.num_batches, 1)

    def test_batch_options(self):
        self.assertEqual(self.presenter.batch_options(),
                         [{'label': 'Batch 0', 'value': 0},
                          {'label': 'Batch 1', 'value': 1},
                          {'label': 'Batch 2', 'value': 2}])

    def test_batch_controls_middle(self):
        (options, prev_disabled, next_disabled,
         remove_disabled, swatch) = self.presenter.batch_controls(1, 3)
        self.assertEqual(len(options), NUM_BATCHES)
        self.assertFalse(prev_disabled)
        self.assertFalse(next_disabled)
        self.assertFalse(remove_disabled)
        self.assertEqual(swatch['backgroundColor'], batch_colour(1))

    def test_batch_controls_ends(self):
        _, prev_disabled, next_disabled, _, _ = \
            self.presenter.batch_controls(0, 3)
        self.assertTrue(prev_disabled)
        self.assertFalse(next_disabled)
        _, prev_disabled, next_disabled, _, _ = \
            self.presenter.batch_controls(2, 3)
        self.assertFalse(prev_disabled)
        self.assertTrue(next_disabled)

    def test_batch_controls_only_batch(self):
        presenter = ControlPanePresenter()
        _, prev_disabled, next_disabled, remove_disabled, _ = \
            presenter.batch_controls(0, 1)
        self.assertTrue(prev_disabled)
        self.assertTrue(next_disabled)
        # the only batch cannot be removed
        self.assertTrue(remove_disabled)

    def test_next_batch(self):
        self.assertEqual(self.presenter.next_batch(1, 0), 1)

    def test_next_batch_at_end(self):
        self.assertEqual(self.presenter.next_batch(1, 2), no_update)

    def test_previous_batch(self):
        self.assertEqual(self.presenter.previous_batch(1, 2), 1)

    def test_previous_batch_at_start(self):
        self.assertEqual(self.presenter.previous_batch(1, 0), no_update)

    def test_add_batch(self):
        active, num_batches = self.presenter.add_batch(1)

        self.assertEqual(num_batches, NUM_BATCHES + 1)
        self.assertEqual(self.presenter.num_batches, NUM_BATCHES + 1)
        self.assertEqual(len(self.data), NUM_BATCHES + 1)
        # the new batch is made active
        self.assertEqual(active, 3)
        # the new batch can be edited
        self.presenter._filters._time.add(3)
        self.assertEqual(list(self.data._dict(3)['time_filters']),
                         ['filter 1'])
        # and shown
        self.assertEqual(len(self.presenter._filters.fill(3)[0]), 1)

    def test_add_batch_no_data(self):
        presenter = ControlPanePresenter()
        self.assertEqual(presenter.add_batch(), (1, 2))
        self.assertEqual(len(presenter._filters._batches), 2)

    def test_remove_batch(self):
        self.data.add_time_filter(2, 'last', 0.1, 0.2)

        active, num_batches = self.presenter.remove_batch(1, 1)

        self.assertEqual(num_batches, NUM_BATCHES - 1)
        self.assertEqual(self.presenter.num_batches, NUM_BATCHES - 1)
        self.assertEqual(len(self.data), NUM_BATCHES - 1)
        self.assertEqual(len(self.presenter._filters._batches),
                         NUM_BATCHES - 1)
        # the next batch becomes active, it has moved down
        self.assertEqual(active, 1)
        self.assertEqual(
            list(self.presenter._filters._time.batch_filters(1)), ['last'])

    def test_remove_last_batch(self):
        active, _ = self.presenter.remove_batch(1, 2)
        # there is no next batch, so the previous one becomes active
        self.assertEqual(active, 1)

    def test_remove_only_batch(self):
        presenter = ControlPanePresenter()
        with self.assertRaises(GUIError):
            presenter.remove_batch(1, 0)
        self.assertEqual(presenter.num_batches, 1)

    def test_remove_batch_no_data(self):
        presenter = ControlPanePresenter(2)
        self.assertEqual(presenter.remove_batch(1, 0), (0, 1))

    def test_remove_renumbers_options(self):
        self.presenter.remove_batch(None, 0)
        self.assertEqual(self.presenter.batch_options(),
                         [{'label': 'Batch 0', 'value': 0},
                          {'label': 'Batch 1', 'value': 1}])

    def test_make_plot_after_remove(self):
        self.presenter.remove_batch(None, 0)
        self.presenter._plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()
        self.presenter.make_plot([], [], False, 1)
        calls = [call[0] for call in
                 self.presenter.add_filter_shading.call_args_list]
        self.assertEqual([call[0] for call in calls], [0, 1])
        self.assertEqual([call[-1] for call in calls], [False, True])


class AddFilterShadingTest(TestHelper):
    """
    Tests for the shaded regions of a single batch.
    """

    def setUp(self):
        self.data = BatchData(FILE, 64, NUM_BATCHES)
        self.presenter = ControlPanePresenter(NUM_BATCHES)
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
        self.assertEqual(self.plot.add_rect.call_args_list,
                         [mock.call(1, 0, 2, 1, '', batch_colour(1),
                                    False, domain=True),
                          mock.call(1, 0.6, 2, 1., '2', batch_colour(1),
                                    False)])
        self.assertEqual(self.plot.add_hline.call_args_list,
                         [mock.call(0.6, row=2, colour=batch_colour(1)),
                          mock.call(1., row=2, colour=batch_colour(1))])


class DisplayHoverTest(TestHelper):

    def setUp(self):
        self.data = BatchData(FILE, 64, NUM_BATCHES)
        self.presenter = ControlPanePresenter(NUM_BATCHES)
        self.presenter.set_data(self.data)
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
        result = self.presenter.display_hover(None)
        self.assertEqual(result, (False, no_update, no_update))

    def test_no_data(self):
        presenter = ControlPanePresenter(NUM_BATCHES)
        result = presenter.display_hover(self.hover)
        self.assertEqual(result, (False, no_update, no_update))

    def test_no_filters(self):
        self.data.set_time_type(1, 'exclude')
        result = self.presenter.display_hover(self.hover)
        self.assertEqual(result[0], True)
        self.assertArrays(result[1], [1, 2, 3, 4])
        self.check_hover_text(result[2], 0.5,
                              ['Batch 0: Keep data: False',
                               'Batch 1: Keep data: True',
                               'Batch 2: Keep data: False'])

    def test_filters_per_batch(self):
        self.data.add_time_filter(0, 'unit', 0.4, 0.6)
        self.data.add_time_filter(0, 'test', 0.2, 0.7)
        self.data.set_time_type(1, 'exclude')
        self.data.add_time_filter(1, 'test', 0.2, 0.7)
        self.data.set_time_type(2, 'exclude')
        self.data.add_time_filter(2, 'unit', 0.4, 0.6)
        result = self.presenter.display_hover(self.hover)
        lines = [child.children for child in result[2].children][3:]
        # the data does not keep the order the filters were added
        self.assertIn(lines[0],
                      ['Batch 0: Keep data: True. Added by: unit, test',
                       'Batch 0: Keep data: True. Added by: test, unit'])
        self.assertEqual(lines[1:],
                         ['Batch 1: Keep data: False. Removed by: test',
                          'Batch 2: Keep data: False. Removed by: unit'])

    def test_not_over_filters(self):
        self.data.add_time_filter(0, 'unit', 0.4, 0.6)
        self.data.set_time_type(1, 'exclude')
        self.data.add_time_filter(1, 'unit', 0.4, 0.6)
        result = self.presenter.display_hover(self.hover_at(0.2))
        self.check_hover_text(result[2], 0.2,
                              ['Batch 0: Keep data: False',
                               'Batch 1: Keep data: True',
                               'Batch 2: Keep data: False'])


if __name__ == '__main__':
    unittest.main()
