import os
import sys
import unittest
from unittest import mock

from MNeuEventLib import BatchData

from MNeuEventGUI.log.presenter import LOG_TABLE, LogPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from MNeuEventGUI.utils.errors import GUIError

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE  # noqa: E402

# range of the sample logs in the test file
TEMP_MIN, TEMP_MAX = 35., 39.
B_MIN, B_MAX = 0.6967067, 1.
I_MIN, I_MAX = 0.4493289, 1.


def make_log_table():
    return [{'Delete_log-table': '',
             'Name_log-table': 'mag_field',
             'sample_log-table': 'B',
             'filter_log-table': 'between',
             'magic': 'between',
             'y0_log-table': 0,
             'yN_log-table': 1,
             'y_min_log-table': 0,
             'y_max_log-table': 3},
            {'Delete_log-table': '',
             'Name_log-table': 'log_default_1',
             'sample_log-table': 'Temp',
             'filter_log-table': 'between',
             'magic': 'between',
             'y0_log-table': 0,
             'yN_log-table': 2,
             'y_min_log-table': 0,
             'y_max_log-table': 3},
            ]


def make_change(row, old, new, name):
    return [{'rowIndex': 0,
             'rowId': '0',
             'data': row,
             'oldValue': old,
             'value': new,
             'colId': name,
             'timestamp': 1}]


def row_index(data, name):
    """
    Get the index of a named row in the table.
    The data does not preserve the order the filters
    were added, so we cannot rely on the row order.
    :param data: the log table data
    :param name: the name of the row
    :returns: the index of the row
    """
    names = [row['Name_log-table'] for row in data]
    return names.index(name)


class LogPresenterTest(TestHelper):

    @mock.patch("MNeuEventGUI.log.presenter.LogView")
    def setUp(self, view):
        self.view = view
        self.view.return_value = mock.Mock()
        self.presenter = LogPresenter()
        self.data = BatchData(FILE, 64, 1)
        self.presenter.set_data(self.data)

    def add_filters(self):
        """
        Add two log filters to the data.
        :returns: the log table data for the filters
        """
        self.data.add_log_filter(0, 'mag_field', 'B', 0.7, 0.9)
        self.data.add_log_filter(0, 'log_default_1', 'Temp', 36., 37.)
        return self.presenter.load(self.data._dict(0)['sample_log_filters'])

    def assertData(self, data, name, log, f_type, y_min, y_max, y0, yN):
        expected = {'Name_log-table': name,
                    'filter_log-table': f_type,
                    'magic': f_type,
                    'sample_log-table': log,
                    'y0_log-table': y0,
                    'yN_log-table': yN,
                    'y_min_log-table': y_min,
                    'y_max_log-table': y_max}
        # the delete button is only in the table, not the loaded data
        data = {key: value for key, value in data.items()
                if key != 'Delete_log-table'}
        self.assertEqual(data.keys(), expected.keys())
        for key in data:
            if isinstance(expected[key], str):
                self.assertEqual(data[key], expected[key])
            else:
                self.assertAlmostEqual(data[key], expected[key], 5)

    def test_init(self):
        self.assertEqual(self.presenter._view,
                         self.view())
        self.assertEqual(self.presenter._defaults,
                         ['Temp_Sample', 'Temp'])

        self.assertEqual(self.presenter._ok_clicks,
                         0)

        self.assertEqual(self.presenter._replace,
                         None)
        self.assertEqual(self.presenter._selected_name,
                         'Temp_Sample')

    def test_set_data(self):
        self.presenter.set_data('data')
        self.assertEqual(self.presenter.data,
                         'data')

    def test_delete_btn_pressed(self):
        table = self.add_filters()
        info = {'colId': 'Delete_log-table',
                'rowIndex': row_index(table, 'log_default_1'),
                'rowId': '1',
                'timestamp': 174}
        data, state = self.presenter.btn_pressed(info, table)
        self.assertFalse(state)
        self.assertEqual(len(data), 1)
        self.assertData(data[0], 'mag_field', 'B', 'between',
                        B_MIN, B_MAX, 0.7, 0.9)
        self.assertEqual(list(self.data._dict(0)['sample_log_filters']),
                         ['mag_field'])

    def test_plot_btn_pressed(self):
        info = {'colId': 'change_btn_log-table',
                'rowIndex': 1,
                'rowId': '1',
                'timestamp': 174}

        data, state = self.presenter.btn_pressed(info, make_log_table())
        self.assertTrue(state)
        self.assertEqual(len(data), 2)
        self.assertData(data[0], 'mag_field', 'B',
                        'between', 0, 3, 0, 1)
        # changes to the default sample log
        self.assertData(data[1], 'log_default_1', 'Temp',
                        'between', 0, 3, 0, 2)
        self.assertEqual(self.presenter._selected_name, 'Temp')
        self.assertEqual(self.presenter._replace, 1)

    def test_get_new_log_name_none(self):
        self.presenter.data = None
        self.assertEqual(self.presenter.get_new_log_name({}),
                         '')

    def test_get_new_log_name_default(self):
        self.assertEqual(self.presenter.get_new_log_name({}),
                         'Temp')

    def test_get_new_log_name_no_default(self):
        self.presenter._defaults = ['not a log']
        # use the first log
        self.assertEqual(self.presenter.get_new_log_name({}),
                         'B')

    def test_get_new_log_name_custom_default(self):
        self.presenter._defaults = ['B']
        self.assertEqual(self.presenter.get_new_log_name({}),
                         'B')

    def test_get_new_log_name_in_use(self):
        # a sample log can be used by multiple filters
        data = [{'sample_log-table': 'Temp'}]
        self.assertEqual(self.presenter.get_new_log_name(data),
                         'Temp')

    def test_get_new_log_name_second_default(self):
        self.presenter._defaults = ['not a log', 'I']
        self.assertEqual(self.presenter.get_new_log_name({}),
                         'I')

    def test_show_log_data(self):
        self.presenter._plot.new_plot = mock.Mock()

        result = self.presenter.show_log_data('B')
        self.assertEqual(result[1], 'Max: 1.000')
        self.assertEqual(result[2], 'Mean: 0.885')
        self.assertEqual(result[3], 'Min: 0.697')
        self.assertEqual(result[4], 'Sigma (std): 0.112')

    def test_selecct_log_new(self):
        options, value = self.presenter.select_log(True, {})
        self.assertArrays(options, ['B', 'I', 'Temp'])
        self.assertEqual(value, 'Temp')

    def test_selecct_log_new_with_filters(self):
        # all logs are available, even if in use
        data = [{'sample_log-table': 'Temp'}]
        options, value = self.presenter.select_log(True, data)
        self.assertArrays(options, ['B', 'I', 'Temp'])
        self.assertEqual(value, 'Temp')

    def test_selecct_log_replace(self):
        data = [{'sample_log-table': 'B'}]
        self.presenter._replace = 0
        self.presenter._selected_name = 'B'
        options, value = self.presenter.select_log(True, data)
        self.assertArrays(options, ['B', 'I', 'Temp'])
        self.assertEqual(value, 'B')

    def test_close_modal_cancel_pressed(self):
        table = self.add_filters()
        state, result = self.presenter.close_modal(0,
                                                   1,
                                                   'Temp',
                                                   table)
        self.assertFalse(state)
        self.assertEqual(result, table)

    def test_close_modal_ok_new_row(self):
        table = self.add_filters()
        state, result = self.presenter.close_modal(1,
                                                   1,
                                                   'Temp',
                                                   table)
        self.assertFalse(state)
        self.assertEqual(len(result), 3)
        self.assertData(result[row_index(result, 'mag_field')],
                        'mag_field', 'B', 'between',
                        B_MIN, B_MAX, 0.7, 0.9)
        self.assertData(result[row_index(result, 'log_default_1')],
                        'log_default_1', 'Temp', 'between',
                        TEMP_MIN, TEMP_MAX, 36, 37)
        # new filter keeps all of the data
        self.assertData(result[row_index(result, 'filter 1')],
                        'filter 1', 'Temp', 'between',
                        TEMP_MIN, TEMP_MAX, TEMP_MIN, TEMP_MAX)

    def test_close_modal_ok_replace_row(self):
        table = self.add_filters()
        self.presenter._replace = row_index(table, 'log_default_1')
        state, result = self.presenter.close_modal(1,
                                                   1,
                                                   'I',
                                                   table)
        self.assertFalse(state)
        self.assertEqual(len(result), 2)
        self.assertData(result[row_index(result, 'mag_field')],
                        'mag_field', 'B', 'between',
                        B_MIN, B_MAX, 0.7, 0.9)
        # updates y values (filter + limits)
        self.assertData(result[row_index(result, 'log_default_1')],
                        'log_default_1', 'I', 'between',
                        I_MIN, I_MAX, I_MIN, I_MAX)

    def test_close_modal_ok_multiple_clicks(self):
        data = []

        state, data = self.presenter.close_modal(1,
                                                 1,
                                                 'Temp',
                                                 data)
        state, data = self.presenter.close_modal(1,
                                                 2,
                                                 'I',
                                                 data)
        state, data = self.presenter.close_modal(2,
                                                 2,
                                                 'B',
                                                 data)
        self.assertFalse(state)
        self.assertEqual(len(data), 2)
        self.assertData(data[row_index(data, 'filter 1')],
                        'filter 1', 'Temp', 'between',
                        TEMP_MIN, TEMP_MAX, TEMP_MIN, TEMP_MAX)
        self.assertData(data[row_index(data, 'filter 2')],
                        'filter 2', 'B', 'between',
                        B_MIN, B_MAX, B_MIN, B_MAX)

    def test_add(self):
        data = [{'Delete_log-table': '',
                 'Name_log-table': 'mag_field',
                 'sample_log-table': 'B'}]

        self.presenter._replace = 0
        self.presenter._selected_name = 'B'

        state, name = self.presenter.add(1, data)
        self.assertTrue(state)
        self.assertEqual(name, 'Temp')
        self.assertEqual(self.presenter._selected_name,
                         'Temp')
        self.assertEqual(self.presenter._replace,
                         None)

    def test__validate_row(self):
        """
        for reference the default values are:
        'y0_log-table': 0,
        'yN_log-table': 1,
        'y_min_log-table': -1,
        'y_max_log-table': 3},

        test_cases is [old, new, name, filter type,
        value for other filter, name
        of other filter, if an error message is expected
        0: no error,
        1: error,
        2: no error, but different value is reset]
        """
        test_cases = [
                      # test for y0
                      # passes
                      [0, .5, 'y0_log-table', 'between', 1, 'yN_log-table', 0],
                      # below min value
                      [0, -2, 'y0_log-table', 'between', 1, 'yN_log-table', 1],
                      # above max value
                      [0, 9, 'y0_log-table', 'between', 1, 'yN_log-table', 1],
                      # above filter, between yN and max
                      [0, 2., 'y0_log-table', 'above', 3, 'yN_log-table', 0],
                      # check not updated if not used
                      [1, 1.2, 'yN_log-table', 'below', 0, 'y0_log-table', 3],
                      # tests for yN
                      # passes
                      [1, 1.3, 'yN_log-table', 'between', 0,
                       'y0_log-table', 0],
                      # below min value
                      [1, -2, 'yN_log-table', 'between', 0, 'y0_log-table', 1],
                      # above max value
                      [1, 9, 'yN_log-table', 'between', 0, 'y0_log-table', 1],
                      # below filter, between y0 and min
                      [1, -.5, 'yN_log-table', 'below', -1, 'y0_log-table', 0],
                      # check not updated if not used
                      [0, -.5, 'y0_log-table', 'above', 1, 'yN_log-table', 0],
                      ]
        for case in test_cases:
            with self.subTest(case=case):
                # set up
                table = make_log_table()
                table[0]['y_min_log-table'] = -1
                # make sure table has correct filter values
                table[0]['magic'] = case[3]
                table[0]['filter_log-table'] = case[3]
                # table should have new value
                table[0][case[2]] = case[1]
                # make change dict
                change = make_change(table[0],
                                     case[0],
                                     case[1],
                                     case[2])

                # run validation
                if case[-1] == 1:
                    # an invalid edit is raised, the reverted
                    # table data is carried on the error
                    with self.assertRaises(GUIError) as context:
                        self.presenter.validate_row(change, table)
                    err = context.exception
                    data = err.revert[LOG_TABLE]['rowData']
                else:
                    data = self.presenter.validate_row(change,
                                                       table)
                # check if the other limit is as expected
                self.assertEqual(data[0][case[5]],
                                 case[4])
                # if no error
                if case[-1] == 0:
                    # success
                    self.assertEqual(data[0][case[2]],
                                     case[1])

                elif case[-1] == 1:
                    # check an error is produced
                    self.assertGreater(len(str(err)), 0)
                    # check value is reverted
                    self.assertEqual(data[0][case[2]],
                                     case[0])

                elif case[-1] == 2:
                    # silently fixes unused filter
                    # check value is reverted
                    self.assertEqual(data[0][case[5]],
                                     case[4])
                    # check keep new value
                    self.assertEqual(data[0][case[2]],
                                     case[1])


if __name__ == '__main__':
    unittest.main()
