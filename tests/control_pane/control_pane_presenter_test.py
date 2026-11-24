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
from MNeuEventGUI.utils.batch_callback import registered
from MNeuEventGUI.utils.errors import GUIError

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE  # noqa: E402

# the tests use several batches
NUM_BATCHES = 3

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

        self.presenter = ControlPanePresenter(NUM_BATCHES)
        self.presenter.set_data(self.data)

        self.presenter.make_plot(empty_tables(),
                                 tables(b0=[TEMP_ROW, B_ROW]),
                                 [False] * NUM_BATCHES,
                                 0)

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
            self.assertEqual(filter_presenter._time.data, None)
            self.assertEqual(filter_presenter._log.data, None)
            self.assertEqual(filter_presenter._amp.data, None)
            self.assertEqual(filter_presenter._hist_settings.data, None)

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
                                 [False] * NUM_BATCHES, 0)
        self.presenter.add_filter_shading.assert_not_called()

        self.assertMockOnce(self.presenter._plot.plot,
                            [[''],
                             [[1]],
                             [[1]]])

    def test_make_plot_empty_filters(self):
        self.presenter._plot.new_plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()

        self.presenter.make_plot(empty_tables(), empty_tables(),
                                 [False] * NUM_BATCHES, 0)

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
                                 [False] * NUM_BATCHES, 1)

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
                                 [False] * NUM_BATCHES, 0)

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
                                 [False] * NUM_BATCHES, 0)

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
        N_strs = self.presenter.calculate([1, None, None])
        self.assertEqual([N.children for N in N_strs],
                         ['Events in this batch: 64,147',
                          'Events in this batch: 7,944',
                          'Events in this batch: 64,147'])

    def test_calculate_without_new_click(self):
        # Dash runs it when a batch is added, the new button
        # has no clicks and the others have not changed
        self.presenter.calculate([1, None, None])
        self.presenter.add_batch()
        data = mock.Mock()
        self.presenter._data = data

        result = self.presenter.calculate([1, None, None, None])
        self.assertIs(result, no_update)
        data.calculate.assert_not_called()

    def test_calculate_after_removing_a_batch(self):
        data = mock.Mock()
        self.presenter._data = data
        self.presenter.calculate([None, 2, None])
        self.presenter.remove_batch(None, 0)
        data.calculate.reset_mock()

        # the counts follow the batch, not its index
        self.assertIs(self.presenter.calculate([2, None]), no_update)
        self.presenter.calculate([2, 1])
        data.calculate.assert_called_once()

    def test_calculate_new_batch_with_no_data(self):
        self.presenter.clear()
        self.presenter.add_batch()
        self.assertIs(self.presenter.calculate([None] * 4), no_update)

    def test_calculate_click_with_no_data(self):
        self.presenter.clear()
        with self.assertRaises(GUIError):
            self.presenter.calculate([1, None, None])

    def test_calculate_with_error(self):
        data = mock.Mock()
        data.calculate.side_effect = RuntimeError("mock throw")
        self.presenter._data = data
        # the global error handler reports this to the user
        with self.assertRaises(RuntimeError):
            self.presenter.calculate([1, None, None])

    def test_refresh(self):
        self.data.set_time_type(1, 'exclude')
        self.data.add_time_filter(1, 'first', 0.01, 0.02)
        self.data.set_amps_baseline(1, 2.7)
        self.data.set_histogram_settings(1, 0.5, 15.22, 1024)

        values = self.presenter.refresh()
        for column in values:
            self.assertEqual(len(column), NUM_BATCHES)

        (data, log_data, amp, state,
         min_time, max_time,
         num_bins, cols) = [column[1] for column in values]

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
        self.assertEqual(values[3][0], 'Include')


def patch_operations(patch):
    """
    :param patch: a Dash Patch
    :returns: the (operation, location) of each change in the patch
    """
    return [(op['operation'], op['location'])
            for op in patch.to_plotly_json()['operations']]


def patch_values(patch):
    """
    :param patch: a Dash Patch
    :returns: the value of each change in the patch
    (None if it does not have one)
    """
    return [op['params'].get('value')
            for op in patch.to_plotly_json()['operations']]


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

    def test_batch_keys(self):
        self.assertEqual(self.presenter.batch_keys, [0, 1, 2])
        self.assertEqual(self.presenter.order(), [0, 1, 2])

    def test_index_of(self):
        self.assertEqual(self.presenter.index_of(2), 2)

    def test_index_of_unknown(self):
        self.assertEqual(self.presenter.index_of(None), 0)

    def test_active_index(self):
        self.assertEqual(self.presenter.active_index(2), 2)

    def test_active_index_unknown(self):
        # e.g. a batch that has just been removed
        with self.assertRaises(GUIError):
            self.presenter.active_index(7)

    def test_new_presenter_forgets_old_batches(self):
        old = self.presenter._filters[2]
        self.assertIs(registered(old), old)
        new = ControlPanePresenter(1)
        # the new control pane only has batch 0
        self.assertIsNone(registered(old))
        self.assertIs(registered(new._filters[0]), new._filters[0])

    def test_batch_options(self):
        self.assertEqual(self.presenter.batch_options(),
                         [{'label': 'Batch 0', 'value': 0},
                          {'label': 'Batch 1', 'value': 1},
                          {'label': 'Batch 2', 'value': 2}])

    def test_batch_controls_middle(self):
        (options, prev_disabled, next_disabled,
         remove_disabled, swatch) = self.presenter.batch_controls(1, None)
        self.assertEqual(len(options), NUM_BATCHES)
        self.assertFalse(prev_disabled)
        self.assertFalse(next_disabled)
        self.assertFalse(remove_disabled)
        self.assertEqual(swatch['backgroundColor'], batch_colour(1))

    def test_batch_controls_ends(self):
        _, prev_disabled, next_disabled, _, _ = \
            self.presenter.batch_controls(0, None)
        self.assertTrue(prev_disabled)
        self.assertFalse(next_disabled)
        _, prev_disabled, next_disabled, _, _ = \
            self.presenter.batch_controls(2, None)
        self.assertFalse(prev_disabled)
        self.assertTrue(next_disabled)

    def test_batch_controls_only_batch(self):
        presenter = ControlPanePresenter()
        _, prev_disabled, next_disabled, remove_disabled, _ = \
            presenter.batch_controls(0, None)
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

    def test_step_needs_new_click(self):
        self.assertEqual(self.presenter.next_batch(1, 0), 1)
        # Dash re-triggering the callback is not a new click
        self.assertEqual(self.presenter.next_batch(1, 1), no_update)
        self.assertEqual(self.presenter.next_batch(2, 1), 2)

    def test_next_batch_skips_removed_keys(self):
        self.presenter.remove_batch(None, 1)
        self.assertEqual(self.presenter.next_batch(1, 0), 2)

    def test_show_batch(self):
        self.assertEqual(self.presenter.show_batch(1),
                         [{'display': 'none'}, None, {'display': 'none'}])

    def test_add_batch(self):
        panes, active, keys = self.presenter.add_batch(1)

        self.assertEqual(self.presenter.num_batches, NUM_BATCHES + 1)
        self.assertEqual(len(self.data), NUM_BATCHES + 1)
        self.assertEqual(keys, [0, 1, 2, 3])
        # the new batch is made active
        self.assertEqual(active, 3)
        # the other batches are hidden in the same change
        self.assertEqual(patch_operations(panes),
                         [('Assign', [0, 'props', 'style']),
                          ('Assign', [1, 'props', 'style']),
                          ('Assign', [2, 'props', 'style']),
                          ('Append', [])])
        self.assertEqual(patch_values(panes)[:3], [{'display': 'none'}] * 3)

        new = self.presenter._filters[-1]
        self.assertEqual(new.batch, NUM_BATCHES)
        self.assertEqual(new._time.data, self.data)
        # the new batch can be edited
        new._time.add()
        self.assertEqual(list(self.data._dict(3)['time_filters']),
                         ['filter 1'])

    def test_add_batch_needs_new_click(self):
        self.presenter.add_batch(1)
        self.assertEqual(self.presenter.add_batch(1), (no_update,) * 3)
        self.assertEqual(self.presenter.num_batches, NUM_BATCHES + 1)

    def test_add_batch_no_data(self):
        presenter = ControlPanePresenter()
        presenter.add_batch()
        self.assertEqual(presenter.batch_keys, [0, 1])

    def test_remove_batch(self):
        self.data.add_time_filter(2, 'last', 0.1, 0.2)

        panes, active, keys = self.presenter.remove_batch(1, 1)

        self.assertEqual(keys, [0, 2])
        self.assertEqual(len(self.data), NUM_BATCHES - 1)
        # the next batch becomes active
        self.assertEqual(active, 2)
        # the new active batch is shown in the same change
        self.assertEqual(patch_operations(panes),
                         [('Delete', [1]), ('Assign', [1, 'props', 'style'])])
        self.assertEqual(patch_values(panes), [None, None])

        # the last batch has moved down, but keeps its IDs
        last = self.presenter._filters[1]
        self.assertEqual(last.batch, 1)
        self.assertEqual(last._time.batch, 1)
        self.assertEqual(last._time.component_id(),
                         {'type': 'time-table', 'batch': 2})
        self.assertEqual(list(last._time.batch_filters), ['last'])

    def test_remove_last_batch(self):
        panes, active, _ = self.presenter.remove_batch(1, 2)
        # there is no next batch, so the previous one becomes active
        self.assertEqual(active, 1)
        self.assertEqual(patch_operations(panes),
                         [('Delete', [2]), ('Assign', [1, 'props', 'style'])])

    def test_remove_batch_needs_new_click(self):
        self.presenter.remove_batch(1, 2)
        self.assertEqual(self.presenter.remove_batch(1, 1), (no_update,) * 3)
        self.assertEqual(self.presenter.num_batches, NUM_BATCHES - 1)

    def test_remove_unknown_batch(self):
        self.assertEqual(self.presenter.remove_batch(1, 9), (no_update,) * 3)
        self.assertEqual(self.presenter.num_batches, NUM_BATCHES)

    def test_remove_only_batch(self):
        presenter = ControlPanePresenter()
        with self.assertRaises(GUIError):
            presenter.remove_batch(1, 0)
        self.assertEqual(presenter.num_batches, 1)

    def test_remove_then_add_batch(self):
        self.presenter.remove_batch(None, 1)
        _, _, keys = self.presenter.add_batch()
        # keys are not reused, so the IDs stay unique
        self.assertEqual(keys, [0, 2, 3])
        self.assertEqual(self.presenter._filters[-1].batch, 2)

    def test_remove_renumbers_options(self):
        self.presenter.remove_batch(None, 0)
        self.assertEqual(self.presenter.batch_options(),
                         [{'label': 'Batch 0', 'value': 1},
                          {'label': 'Batch 1', 'value': 2}])

    def test_remove_batch_stops_its_callbacks(self):
        removed = self.presenter._filters[1]._time
        self.assertIs(registered(removed), removed)
        self.presenter.remove_batch(None, 1)
        self.assertIsNone(registered(removed))

    def test_make_plot_after_remove(self):
        self.presenter.remove_batch(None, 0)
        self.presenter._plot = mock.Mock()
        self.presenter.add_filter_shading = mock.Mock()
        self.presenter.make_plot(tables()[:2], tables()[:2],
                                 [False] * 2, 2)
        # the active batch (key 2) is now index 1, so it is drawn last
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
        self.presenter = ControlPanePresenter(NUM_BATCHES)
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
                               'Added by: unit, test',
                               'Batch 1: Keep data: False. '
                               'Removed by: test',
                               'Batch 2: Keep data: False. '
                               'Removed by: unit'])

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
