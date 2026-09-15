import unittest
from unittest import mock
from MuonDataLib.GUI.table.column import (TableGroup,
                                          TextColumn,
                                          NumericColumn,
                                          TableColumns)
from MuonDataLib.GUI.table.presenter import TablePresenter
from MuonDataLib.test_helpers.unit_test import TestHelper


NAME = 'Name_table_test'


class TablePresenterMock(TablePresenter):
    @property
    def default_row(self):
        return {'Data': 42}


class TablePresenterTest(TestHelper):

    @mock.patch("MuonDataLib.GUI.table.presenter.TableView")
    def setUp(self, view):
        self.view = view
        self.view.return_value = 'widget'
        cols = TableColumns([TableGroup([TextColumn(NAME, 'name')]),
                             TableGroup([NumericColumn('Data', 'data')])],
                            False)
        self.presenter = TablePresenterMock('table_test',
                                            cols,
                                            NAME)

    def assert_data(self, result, name, value):
        self.assertEqual(result, {'Delete_table_test': '',
                                  NAME: name,
                                  'Data': value})

    def test_set_view(self):
        self.view.assert_called_once()

    def test_add_empty(self):
        data = []
        result = self.presenter.add(0, data)
        self.assertEqual(len(result), 1)
        self.assert_data(result[0], 'default_1', 42)

    def test_add_None(self):
        data = None
        result = self.presenter.add(0, data)
        self.assertEqual(len(result), 1)
        self.assert_data(result[0], 'default_1', 42)

    def test_add(self):
        data = [{'Delete_table_test': '',
                 NAME: 'keep row',
                 'Data': 30},
                {'Delete_table_test': '',
                 NAME: 'old row',
                 'Data': 21}
                ]

        result = self.presenter.add(0, data)
        self.assertEqual(len(result), 3)
        self.assert_data(result[0], 'keep row', 30)

        self.assert_data(result[1], 'old row', 21)

        self.assert_data(result[2], 'default_1', 42)

    def test_validate(self):
        row = [{'rowIndex': 0, 'rowId': '0',
                'data': {'Delete_table_test': '',
                         NAME: 'default',
                         'Data': 42},
                'oldValue': 'default_1',
                'value': 'default',
                'colId': NAME,
                'timestamp': 19}]
        data = self.presenter.add(0, [])
        data = self.presenter.add(0, data)
        self.assertEqual(len(data), 2)

        data, err = self.presenter.validate(row, data)

        self.assertEqual(err, '')
        self.assertEqual(len(data), 2)

        self.assert_data(data[0], 'default', 42)
        self.assert_data(data[1], 'default_2', 42)

    def test_validate_fails(self):
        data = self.presenter.add(0, [])
        data = self.presenter.add(0, data)
        self.assertEqual(len(data), 2)

        data[1][NAME] = data[0][NAME]

        row = [{'rowIndex': 1, 'rowId': '1',
                'data': {'Delete_table_test': '',
                         NAME: data[0][NAME],
                         'Data': 42},
                'oldValue': 'default_2',
                'value': data[0][NAME],
                'colId': NAME,
                'timestamp': 19}]

        data, err = self.presenter.validate(row, data)

        self.assertEqual(err, 'Repeated name default_1')
        self.assertEqual(len(data), 2)

        self.assert_data(data[0], 'default_1', 42)
        self.assert_data(data[1], 'default_2', 42)

    def test_validate_row(self):
        """
        There are no checks in validate_rows, so no need
        to test repeated name (done in validate)
        """
        row = [{'rowIndex': 0, 'rowId': '0',
                'data': {'Delete_table_test': '',
                         NAME: 'default',
                         'Data': 42},
                'oldValue': 'default_1',
                'value': 'default',
                'colId': NAME,
                'timestamp': 19}]
        data = self.presenter.add(0, [])
        data = self.presenter.add(0, data)
        self.assertEqual(len(data), 2)

        data, err = self.presenter.validate_row(row, data)

        self.assertEqual(err, '')
        self.assertEqual(len(data), 2)

        self.assert_data(data[0], 'default', 42)
        self.assert_data(data[1], 'default_2', 42)

    def test_delete_row(self):
        """
        There are no checks in validate_rows, so no need
        to test repeated name (done in validate)
        """
        info = {'colId': 'Delete_time-table',
                'rowIndex': 1,
                'rowId': '1',
                'timestamp': 174}

        data = self.presenter.add(0, [])
        data = self.presenter.add(0, data)
        data = self.presenter.add(0, data)

        self.assertEqual(len(data), 3)

        data = self.presenter.delete_row(info, data)

        self.assertEqual(len(data), 2)

        self.assert_data(data[0], 'default_1', 42)
        self.assert_data(data[1], 'default_3', 42)

    def test_get_next_row_name(self):
        self.assertEqual(self.presenter.get_next_row_name,
                         'default_1')
        self.assertEqual(self.presenter.get_next_row_name,
                         'default_2')
        self.assertEqual(self.presenter.get_next_row_name,
                         'default_3')

    def test_generate_default(self):
        data = self.presenter.generate_default
        self.assert_data(data, 'default_1', 42)

    def test__delete_row_col(self):
        delete_btn_dict = self.presenter._delete_row_col
        self.assertEqual(delete_btn_dict,
                         {'field': 'Delete_t',
                          'headerName': '',
                          'width': 100,
                          'editable': False,
                          'cellRenderer': 'Button',
                          'cellRendererParams': {'Icon': 'bi bi-trash me-2',
                                                 'className': 'btn btn-danger'}
                          })


if __name__ == '__main__':
    unittest.main()
