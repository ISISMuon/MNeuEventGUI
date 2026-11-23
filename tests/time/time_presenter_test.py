import os
import sys
import unittest
from unittest import mock

from MNeuEventLib import BatchData

from MNeuEventGUI.test_helpers.unit_test import TestHelper
from MNeuEventGUI.time.presenter import TimePresenter
from MNeuEventGUI.utils.errors import GUIError

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE  # noqa: E402


def get_validation_data_end(new_value):
    change = [{'rowIndex': 1,
               'rowId': '1',
               'data': {'Delete_time-table': '',
                        'Name_time-table': 'default_2',
                        'Start_time-table': 800,
                        'End_time-table': new_value},
               'oldValue': 1100,
               'value': new_value,
               'colId': 'End_time-table',
               'timestamp': 10}]

    data = [{'Delete_time-table': '',
             'Name_time-table': 'default_1',
             'Start_time-table': 400,
             'End_time-table': 600},
            {'Delete_time-table': '',
             'Name_time-table': 'default_2',
             'Start_time-table': 800,
             'End_time-table': new_value}]

    return change, data


def get_validation_data_start(new_value):
    change = [{'rowIndex': 1,
               'rowId': '1',
               'data': {'Delete_time-table': '',
                        'Name_time-table': 'default_2',
                        'Start_time-table': new_value,
                        'End_time-table': 1100},
               'oldValue': 800,
               'value': new_value,
               'colId': 'Start_time-table',
               'timestamp': 10}]

    data = [{'Delete_time-table': '',
             'Name_time-table': 'default_1',
             'Start_time-table': 400,
             'End_time-table': 600},
            {'Delete_time-table': '',
             'Name_time-table': 'default_2',
             'Start_time-table': new_value,
             'End_time-table': 1100}]

    return change, data


class TimePresenterTest(TestHelper):

    @mock.patch("MNeuEventGUI.time.presenter.TimeView")
    def setUp(self, view):
        self.view = view
        self.presenter = TimePresenter(0)
        self.data = BatchData(FILE, 64, 1)
        self.presenter.set_data(self.data)
        self.presenter.set_time_range(0, 1000)

    def test_set_view(self):
        self.view.assert_called_once()

    def test_set_time_range(self):
        self.assertEqual(self.presenter.start, 0)
        self.assertEqual(self.presenter.end, 1000)

        self.presenter.set_time_range(4.1, 6.7)
        self.assertEqual(self.presenter.start, 4.1)
        self.assertEqual(self.presenter.end, 6.7)

        # check the limits on the cols
        cols = self.presenter.cols.cols[2].get_column_dict
        cols = cols[0]['children']
        for k in range(2):
            data = cols[k]['cellEditorParams']
            self.assertEqual(data['min'], 4.1)
            self.assertEqual(data['max'], 6.7)

    def assert_data_start(self, result, expected):
        _, data = get_validation_data_start(expected)
        self.assertEqual(result, data)

    def assert_data_end(self, result, expected):
        _, data = get_validation_data_end(expected)
        self.assertEqual(result, data)

    def test_validate_row_bad_start(self):
        # if outside data range get None
        for val in [None, 1200, 1100]:
            with self.subTest(val=val):
                change, data = get_validation_data_start(val)
                with self.assertRaises(GUIError) as context:
                    self.presenter.validate_row(change, data)
                self.assert_data_start(
                    context.exception.revert[0][1]['rowData'], 800)
                assert (len(str(context.exception)) > 1)

    def test_validate_row_bad_end(self):
        # if outside data range get None
        for val in [None, 200, 800]:
            with self.subTest(val=val):
                change, data = get_validation_data_end(val)
                with self.assertRaises(GUIError) as context:
                    self.presenter.validate_row(change, data)
                self.assert_data_end(
                    context.exception.revert[0][1]['rowData'], 1100)
                assert (len(str(context.exception)) > 1)

    def test_validate_pass_stat(self):
        change, data = get_validation_data_start(900)
        result = self.presenter.validate_row(change, data)
        self.assert_data_start(result, 900)

    def test_validate_pass_end(self):
        change, data = get_validation_data_end(900)
        result = self.presenter.validate_row(change, data)
        self.assert_data_end(result, 900)

    def test_add(self):
        data = self.presenter.add()
        self.assertEqual(data,
                         [{'Name_time-table': 'filter 1',
                           'Start_time-table': 330,
                           'End_time-table': 660}])

    def test_add_updated_range(self):
        self.presenter.set_time_range(1, 200)
        data = self.presenter.add()
        self.assertEqual(data,
                         [{'Name_time-table': 'filter 1',
                           'Start_time-table': 66,
                           'End_time-table': 132}])

    def add_filters(self):
        """
        Add two time filters to the data.
        :returns: the time table data for the filters
        """
        self.data.add_time_filter(0, 'default_1', 200, 400)
        self.data.add_time_filter(0, 'default_2', 800, 1000)
        return self.presenter.load(self.data._dict(0)['time_filters'])

    def edit_info(self, table, name, **new_values):
        """
        Create the Dash edit info for a row in the table.
        :param table: the time table data
        :param name: the name of the row to edit
        :param new_values: the new values for the row,
        keyed by column ID
        :returns: the edit info
        """
        row = [r['Name_time-table'] for r in table].index(name)
        return [{'rowIndex': row,
                 'rowId': str(row),
                 'data': {**table[row], **new_values},
                 'colId': next(iter(new_values)),
                 'timestamp': 1}]

    def test_edit_row_values(self):
        table = self.add_filters()
        info = self.edit_info(table, 'default_2',
                              **{'Start_time-table': 700,
                                 'End_time-table': 900})
        result = self.presenter.edit_row(info, table)

        self.assertCountEqual(result, [{'Name_time-table': 'default_1',
                                        'Start_time-table': 200,
                                        'End_time-table': 400},
                                       {'Name_time-table': 'default_2',
                                        'Start_time-table': 700,
                                        'End_time-table': 900}])

    def test_edit_row_rename(self):
        table = self.add_filters()
        info = self.edit_info(table, 'default_1',
                              **{'Name_time-table': 'renamed'})
        result = self.presenter.edit_row(info, table)

        self.assertCountEqual(result, [{'Name_time-table': 'renamed',
                                        'Start_time-table': 200,
                                        'End_time-table': 400},
                                       {'Name_time-table': 'default_2',
                                        'Start_time-table': 800,
                                        'End_time-table': 1000}])
        self.assertEqual(sorted(self.data._dict(0)['time_filters']),
                         ['default_2', 'renamed'])

    def test_get_range(self):
        row = {'Delete_time-table': '',
               'Name_time-table': 'default_1',
               'Start_time-table': 100,
               'End_time-table': 200}
        result = self.presenter.get_range(row)
        self.assertArrays(result, [100, 200])

    def test_set_state(self):
        cols = self.presenter.cols.get_column_dict
        self.assertEqual(cols[2]['headerName'],
                         'Include Filter details')

        for state in ['Exclude', 'Include']:
            with self.subTest(state=state):
                self.presenter.set_state(state)
                cols = self.presenter.cols.get_column_dict
                self.assertEqual(cols[2]['headerName'],
                                 f'{state} Filter details')
                self.assertEqual(self.data._dict(0)['time_filter_type'],
                                 state)

    def test_update_state(self):
        for state, changed in [('Exclude', False), ('Include', True)]:
            with self.subTest(state=state):
                cols, signal = self.presenter.update_state(state, changed)
                self.assertEqual(cols[2]['headerName'],
                                 f'{state} Filter details')
                self.assertEqual(self.data._dict(0)['time_filter_type'],
                                 state)
                # the signal is flipped, so that it always reports a change
                self.assertEqual(signal, not changed)

    def test_load(self):
        filters = {'default_1': {'start': 200, 'end': 400},
                   'default_2': {'start': 800, 'end': 1000}}

        data = self.presenter.load(filters)

        self.assertEqual(data, [{'Name_time-table': 'default_1',
                                 'Start_time-table': 200,
                                 'End_time-table': 400},
                                {'Name_time-table': 'default_2',
                                 'Start_time-table': 800,
                                 'End_time-table': 1000}])

    def test_load_empty(self):
        self.assertEqual(self.presenter.load({}), [])


class TimePresenterBatchTest(TestHelper):
    """
    Check that the presenter only changes the
    filters for its own batch.
    """

    @mock.patch("MNeuEventGUI.time.presenter.TimeView")
    def setUp(self, view):
        self.presenter = TimePresenter(batch=1)
        self.data = BatchData(FILE, 64, 2)
        self.presenter.set_data(self.data)
        self.presenter.set_time_range(0, 1000)

    def assert_batch_0_unchanged(self):
        self.assertEqual(self.data._dict(0)['time_filters'], {})

    def test_batch(self):
        self.assertEqual(self.presenter.batch, 1)

    def test_add(self):
        self.presenter.add()
        self.assertEqual(list(self.data._dict(1)['time_filters']),
                         ['filter 1'])
        self.assert_batch_0_unchanged()

    def test_add_name_in_use(self):
        self.data.add_time_filter(1, 'filter 1', 200, 400)
        self.presenter.add()
        self.assertEqual(sorted(self.data._dict(1)['time_filters']),
                         ['filter 1', 'filter 2'])

    def test_delete_row(self):
        self.data.add_time_filter(1, 'default_1', 200, 400)
        table = self.presenter.load(self.data._dict(1)['time_filters'])
        result = self.presenter.delete_row({'rowIndex': 0}, table)
        self.assertEqual(result, [])
        self.assertEqual(self.data._dict(1)['time_filters'], {})

    def test_edit_row(self):
        self.data.add_time_filter(1, 'default_1', 200, 400)
        table = self.presenter.load(self.data._dict(1)['time_filters'])
        info = [{'rowIndex': 0,
                 'data': {**table[0], 'End_time-table': 500}}]
        self.presenter.edit_row(info, table)
        self.assertEqual(self.data._dict(1)['time_filters']['default_1'],
                         {'start': 200, 'end': 500})
        self.assert_batch_0_unchanged()

    def test_edit_row_rename(self):
        self.data.add_time_filter(1, 'default_1', 200, 400)
        table = self.presenter.load(self.data._dict(1)['time_filters'])
        info = [{'rowIndex': 0,
                 'data': {**table[0], 'Name_time-table': 'renamed'}}]
        self.presenter.edit_row(info, table)
        self.assertEqual(list(self.data._dict(1)['time_filters']),
                         ['renamed'])
        self.assert_batch_0_unchanged()

    def test_set_state(self):
        self.presenter.set_state('Exclude')
        self.assertEqual(self.data._dict(1)['time_filter_type'], 'Exclude')
        self.assertEqual(self.data._dict(0)['time_filter_type'], 'Include')

    def test_validate_row_error_has_batch(self):
        change, data = get_validation_data_start(1200)
        with self.assertRaises(GUIError) as context:
            self.presenter.validate(change, data)
        self.assertTrue(str(context.exception).startswith('Batch 1: '))
        # the reverted data goes back to this batch's table
        [(component_id, _)] = context.exception.revert
        self.assertEqual(component_id, self.presenter.component_id())


if __name__ == '__main__':
    unittest.main()
