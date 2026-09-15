import unittest
from unittest import mock
from MuonDataLib.GUI.time.presenter import TimePresenter
from MuonDataLib.test_helpers.unit_test import TestHelper
from MuonDataLib.filters import TimeFilters, Filter


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

    @mock.patch("MuonDataLib.GUI.time.presenter.TimeView")
    def setUp(self, view):
        self.view = view
        self.presenter = TimePresenter()

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

    def test_default_row(self):
        row = self.presenter.default_row
        self.assertEqual(row,
                         {'Start_time-table': 330,
                          'End_time-table': 660})

    def test_default_row_updated(self):
        self.presenter.set_time_range(1, 200)
        row = self.presenter.default_row
        self.assertEqual(row,
                         {'Start_time-table': 66,
                          'End_time-table': 132})

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

        self.presenter.set_state('Include')
        cols = self.presenter.cols.get_column_dict
        self.assertEqual(cols[2]['headerName'],
                         'Include Filter details')

    def test_display_confirm_empty_table(self):
        self.assertEqual(self.presenter._previous, 'Exclude')
        show, cols = self.presenter.display_confirm('Include', [])
        self.assertEqual(self.presenter._previous, 'Include')
        self.assertFalse(show)

        # just check the updated part
        self.assertEqual(cols[2]['headerName'],
                         'Include Filter details')

    def test_display_confirm(self):
        self.assertEqual(self.presenter._previous, 'Exclude')
        _, data = get_validation_data_start(800)

        show, cols = self.presenter.display_confirm('Include', data)
        self.assertEqual(self.presenter._previous, 'Exclude')
        self.assertTrue(show)

        # just check the updated part
        self.assertEqual(cols[2]['headerName'],
                         'Exclude Filter details')

    def test_confirm(self):
        _, data = get_validation_data_start(800)
        self.assertEqual(self.presenter._previous, 'Exclude')

        state, data, cols, change = self.presenter.confirm(4,
                                                           1,
                                                           'Include',
                                                           data)

        self.assertEqual(self.presenter._previous, 'Include')
        self.assertEqual(data, [])
        self.assertEqual(cols[2]['headerName'],
                         'Include Filter details')
        self.assertTrue(change)

    def test_confirm_cancel(self):
        _, data_in = get_validation_data_start(800)
        self.assertEqual(self.presenter._previous, 'Exclude')

        state, data, cols, change = self.presenter.confirm(1,
                                                           3,
                                                           'Include',
                                                           data_in)

        self.assertEqual(self.presenter._previous, 'Exclude')
        self.assertEqual(data_in, data)
        self.assertEqual(len(data_in), 2)
        self.assertEqual(cols[2]['headerName'],
                         'Exclude Filter details')
        self.assertFalse(change)

    def test_load_keep_filters(self):
        filter_data = TimeFilters(
                          keep_filters = [Filter('default_1', 200, 400),
                                          Filter('default_2', 800, 1000)]
                      )

        data, state = self.presenter.load(filter_data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], {'Name_time-table': 'default_1',
                                   'Start_time-table': 200,
                                   'End_time-table': 400})

        self.assertEqual(data[1], {'Name_time-table': 'default_2',
                                   'Start_time-table': 800,
                                   'End_time-table': 1000})

        self.assertEqual(self.presenter._previous, 'Include')
        self.assertEqual(state, 'Include')

    def test_load_remove_filters(self):
        filter_data = TimeFilters(
                          remove_filters = [Filter('default_1', 200, 400),
                                            Filter('default_2', 800, 1000)]
                      )

        data, state = self.presenter.load(filter_data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], {'Name_time-table': 'default_1',
                                   'Start_time-table': 200,
                                   'End_time-table': 400})

        self.assertEqual(data[1], {'Name_time-table': 'default_2',
                                   'Start_time-table': 800,
                                   'End_time-table': 1000})

        self.assertEqual(self.presenter._previous, 'Exclude')
        self.assertEqual(state, 'Exclude')

    def test_load_fails(self):

        filter_data = TimeFilters(
                          keep_filters = [Filter('default_1', 200, 400)],
                          remove_filters = [Filter('default_2', 800, 1000)]
                      )
        try:
            data, state = self.presenter.load(filter_data)
        except RuntimeError as err:
            self.assertEqual(str(err), 'Cannot have both include and'
                             ' exclude time filters')
            return
        self.fail("should fail for a mixed filter file")


if __name__ == '__main__':
    unittest.main()
