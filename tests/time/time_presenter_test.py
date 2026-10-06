import unittest
from unittest import mock
from MNeuEventGUI.time.presenter import TimePresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from MNeuEventLib import BatchData
import os
import sys

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
        self.presenter = TimePresenter()
        self.data = BatchData(FILE, 64, 1)
        self.presenter.set_data(self.data)

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
                result, err = self.presenter.validate_row(change,
                                                          data)
                self.assert_data_start(result, 800)
                assert (len(err) > 1)

    def test_validate_row_bad_end(self):
        # if outside data range get None
        for val in [None, 200, 800]:
            with self.subTest(val=val):
                change, data = get_validation_data_end(val)
                result, err = self.presenter.validate_row(change,
                                                          data)
                self.assert_data_end(result, 1100)
                assert (len(err) > 1)

    def test_validate_pass_stat(self):
        change, data = get_validation_data_start(900)
        result, err = self.presenter.validate_row(change,
                                                  data)
        self.assert_data_start(result, 900)

    def test_validate_pass_end(self):
        change, data = get_validation_data_end(900)
        result, err = self.presenter.validate_row(change,
                                                  data)
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
                         'Exclude Filter details')

        for state in ['Exclude', 'Include']:
            with self.subTest(state=state):
                self.presenter.set_state(state)
                cols = self.presenter.cols.get_column_dict
                self.assertEqual(cols[2]['headerName'],
                                 f'{state} Filter details')
                self.assertEqual(self.data._dict(0)['time_filter_type'],
                                 state)

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


if __name__ == '__main__':
    unittest.main()
