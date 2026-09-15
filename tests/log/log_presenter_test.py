import unittest
from unittest import mock

from MuonDataLib.GUI.log.presenter import LogPresenter
from MuonDataLib.test_helpers.unit_test import TestHelper
from MuonDataLib.test_helpers.utils import get_sample_logs


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


class LogPresenterTest(TestHelper):

    @mock.patch("MuonDataLib.GUI.log.presenter.LogView")
    def setUp(self, view):
        self.view = view
        self.view.return_value = mock.Mock()
        self.presenter = LogPresenter()
        self.presenter.set_logs(get_sample_logs())

    def assertData(self, data, name, log, f_type, y_min, y_max, y0, yN):
        expected = {'Delete_log-table': '',
                    'Name_log-table': name,
                    'filter_log-table': f_type,
                    'magic': f_type,
                    'sample_log-table': log,
                    'y0_log-table': y0,
                    'yN_log-table': yN,
                    'y_min_log-table': y_min,
                    'y_max_log-table': y_max}
        self.assertEqual(len(data.keys()), len(expected.keys()))
        for key in data.keys():
            self.assertEqual(data[key], expected[key])

    def test_init(self):
        self.presenter._logs = None
        self.assertEqual(self.presenter._view,
                         self.view())
        self.assertEqual(self.presenter._logs,
                         None)
        self.assertEqual(self.presenter._defaults,
                         ['Temp_Sample'])

        self.assertEqual(self.presenter._ok_clicks,
                         0)

        self.assertEqual(self.presenter._replace,
                         None)
        self.assertEqual(self.presenter._selected_name,
                         'Temp_Sample')

    def test_set_logs(self):
        self.presenter.set_logs('logs')
        self.assertEqual(self.presenter._logs,
                         'logs')

    def test_delete_btn_pressed(self):
        info = {'colId': 'Delete_log-table',
                'rowIndex': 1,
                'rowId': '1',
                'timestamp': 174}
        data, state = self.presenter.btn_pressed(info, make_log_table())
        self.assertFalse(state)
        self.assertEqual(len(data), 1)
        self.assertData(data[0], 'mag_field', 'B', 'between', 0, 3, 0, 1)

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

    def test_get_available_logs_empty(self):
        data = {}

        names = self.presenter.get_available_logs(data)
        self.assertArrays(names, ['Temp', 'B', 'I'])

    def test_get_available_logs_with_log_filter(self):
        data = [{'sample_log-table': 'B'}]

        names = self.presenter.get_available_logs(data)
        self.assertArrays(names, ['Temp', 'I'])

    def test_get_available_logs_with_replace_filter(self):
        data = [{'sample_log-table': 'B'},
                {'sample_log-table': 'I'}]
        self.presenter._replace = 1
        self.presenter._selected_name = 'B'

        names = self.presenter.get_available_logs(data)
        self.assertArrays(names, ['Temp', 'B'])

    def test_get_new_log_name_none(self):
        self.presenter._logs = None
        self.assertEqual(self.presenter.get_new_log_name({}),
                         '')

    def test_get_new_log_name_no_default(self):
        self.assertEqual(self.presenter.get_new_log_name({}),
                         'Temp')

    def test_get_new_log_name_default(self):
        self.presenter._defaults = ['B']
        self.assertEqual(self.presenter.get_new_log_name({}),
                         'B')

    def test_get_new_log_name_after_defaults(self):
        self.presenter._defaults = ['B']
        data = [{'sample_log-table': 'B'}]
        self.assertEqual(self.presenter.get_new_log_name(data),
                         'Temp')

    def test_get_new_log_name_second_default(self):
        self.presenter._defaults = ['B', 'I']
        data = [{'sample_log-table': 'B'}]
        self.assertEqual(self.presenter.get_new_log_name(data),
                         'I')

    def test_show_log_data(self):
        self.presenter._plot.new_plot = mock.Mock()

        result = self.presenter.show_log_data('B')
        self.assertEqual(result[1], 'Max: 2.000')
        self.assertEqual(result[2], 'Mean: 1.250')
        self.assertEqual(result[3], 'Min: 0.500')
        self.assertEqual(result[4], 'Sigma (std): 0.559')

    def test_selecct_log_new(self):
        options, value = self.presenter.select_log(True, {})
        self.assertArrays(options, ['Temp', 'B', 'I'])
        self.assertEqual(value, 'Temp')

    def test_selecct_log_new_with_filters(self):
        data = [{'sample_log-table': 'B'}]
        options, value = self.presenter.select_log(True, data)
        self.assertArrays(options, ['Temp', 'I'])
        self.assertEqual(value, 'Temp')

    def test_selecct_log_replace(self):
        data = [{'sample_log-table': 'B'}]
        self.presenter._replace = 1
        self.presenter._selected_name = 'B'
        options, value = self.presenter.select_log(True, data)
        self.assertArrays(options, ['Temp', 'B', 'I'])
        self.assertEqual(value, 'B')

    def test_close_modal_cancel_pressed(self):
        state, result = self.presenter.close_modal(0,
                                                   1,
                                                   'Temp',
                                                   [make_log_table()[0]])
        self.assertFalse(state)
        self.assertEqual(len(result), 1)
        self.assertData(result[0], 'mag_field', 'B', 'between', 0, 3, 0, 1)

    def test_close_modal_ok_new_row(self):
        state, result = self.presenter.close_modal(1,
                                                   1,
                                                   'Temp',
                                                   [make_log_table()[0]])
        self.assertFalse(state)
        self.assertEqual(len(result), 2)
        self.assertData(result[0], 'mag_field', 'B',
                        'between', 0, 3, 0, 1)
        self.assertData(result[1], 'log_default_1', 'Temp',
                        'between', -1.9, -1.6, -1.9, -1.6)

    def test_close_modal_ok_replace_row(self):

        self.presenter._replace = 1
        state, result = self.presenter.close_modal(1,
                                                   1,
                                                   'I',
                                                   make_log_table())
        self.assertFalse(state)
        self.assertEqual(len(result), 2)
        self.assertData(result[0], 'mag_field', 'B',
                        'between', y0=0, yN=1, y_min=0, y_max=3)
        # updates y values (filter + limits)
        self.assertData(result[1], 'log_default_1', 'I',
                        'between', y0=1, yN=4, y_min=1, y_max=4)

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
        self.assertData(data[0], 'log_default_1', 'Temp',
                        'between', -1.9, -1.6, -1.9, -1.6)
        self.assertData(data[1], 'log_default_2', 'B',
                        'between', 0.5, 2, 0.5, 2)

    def test_add(self):
        data = [{'Delete_log-table': '',
                 'Name_log-table': 'mag_field',
                 'sample_log-table': 'B'}]

        self._replace = 0
        self._selected_name = 'B'

        state, name = self.presenter.add(1, data)
        self.assertTrue(state)
        self.assertEqual(name, 'Temp')
        self.assertEqual(self.presenter._selected_name,
                         'Temp')
        self.assertEqual(self.presenter._replace,
                         None)

    def test_generate_default(self):
        data = []
        result = self.presenter.generate_default(data, 'B')
        self.assertData(result, 'log_default_1', 'B', 'between', 0, 1, 0, 1)

    def test_generate_default_multiple_calls(self):
        data = []
        data.append(self.presenter.generate_default(data, 'B'))
        result = self.presenter.generate_default(data, 'I')
        self.assertData(result, 'log_default_2', 'I', 'between', 0, 1, 0, 1)

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
                data, msg = self.presenter.validate_row(change,
                                                        table)
                # check if the other limit is as expected
                self.assertEqual(data[0][case[5]],
                                 case[4])
                # if no error
                if case[-1] == 0:
                    # success
                    self.assertEqual(msg, '')
                    self.assertEqual(data[0][case[2]],
                                     case[1])

                elif case[-1] == 1:
                    # error and reset
                    print(msg)
                    # check an error is produced
                    self.assertGreater(len(msg), 0)
                    # check value is reverted
                    self.assertEqual(data[0][case[2]],
                                     case[0])

                elif case[-1] == 2:
                    # silently fixes unused filter
                    # check an error is produced
                    self.assertEqual(len(msg), 0)
                    # check value is reverted
                    self.assertEqual(data[0][case[5]],
                                     case[4])
                    # check keep new value
                    self.assertEqual(data[0][case[2]],
                                     case[1])


if __name__ == '__main__':
    unittest.main()
