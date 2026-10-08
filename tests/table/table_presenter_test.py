import unittest
from unittest import mock

from MNeuEventGUI.table.column import (
    NumericColumn,
    TableColumns,
    TableGroup,
    TextColumn,
)
from MNeuEventGUI.table.presenter import TablePresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from MNeuEventGUI.utils.errors import GUIError

NAME = 'Name_table_test'


def make_row(name, value):
    return {'Delete_table_test': '',
            NAME: name,
            'Data': value}


class TablePresenterTest(TestHelper):

    @mock.patch("MNeuEventGUI.table.presenter.TableView")
    def setUp(self, view):
        self.view = view
        self.view.return_value = 'widget'
        cols = TableColumns([TableGroup([TextColumn(NAME, 'name')]),
                             TableGroup([NumericColumn('Data', 'data')])],
                            False)
        self.presenter = TablePresenter('table_test',
                                        cols,
                                        NAME)

    def assert_data(self, result, name, value):
        self.assertEqual(result, make_row(name, value))

    def test_set_view(self):
        self.view.assert_called_once()

    def test_add_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.presenter.add()

    def test_delete_row_not_implemented(self):
        info = {'colId': 'Delete_table_test',
                'rowIndex': 0,
                'rowId': '0',
                'timestamp': 174}
        with self.assertRaises(NotImplementedError):
            self.presenter.delete_row(info, [make_row('default_1', 42)])

    def test_edit_row_not_implemented(self):
        info = [{'rowIndex': 0,
                 'data': make_row('default', 42)}]
        with self.assertRaises(NotImplementedError):
            self.presenter.edit_row(info, [make_row('default_1', 42)])

    def test_validate(self):
        row = [{'rowIndex': 0, 'rowId': '0',
                'data': make_row('default', 42),
                'oldValue': 'default_1',
                'value': 'default',
                'colId': NAME,
                'timestamp': 19}]
        data = [make_row('default_1', 42),
                make_row('default_2', 42)]

        data = self.presenter.validate(row, data)

        self.assertEqual(len(data), 2)

        self.assert_data(data[0], 'default', 42)
        self.assert_data(data[1], 'default_2', 42)

    def test_validate_fails(self):
        row = [{'rowIndex': 1, 'rowId': '1',
                'data': make_row('default_1', 42),
                'oldValue': 'default_2',
                'value': 'default_1',
                'colId': NAME,
                'timestamp': 19}]
        data = [make_row('default_1', 42),
                make_row('default_1', 42)]

        with self.assertRaises(GUIError) as context:
            self.presenter.validate(row, data)

        self.assertEqual(str(context.exception),
                         'Repeated name default_1')

        # the corrected data is carried on the error, so the
        # error handler can put it back into the table
        data = context.exception.revert[self.presenter.ID]['rowData']
        self.assertEqual(len(data), 2)

        # the name is reverted
        self.assert_data(data[0], 'default_1', 42)
        self.assert_data(data[1], 'default_2', 42)

    def test_validate_row(self):
        """
        There are no checks in validate_rows, so no need
        to test repeated name (done in validate)
        """
        row = [{'rowIndex': 0, 'rowId': '0',
                'data': make_row('default', 42),
                'oldValue': 'default_1',
                'value': 'default',
                'colId': NAME,
                'timestamp': 19}]
        data = [make_row('default_1', 42),
                make_row('default_2', 42)]

        data = self.presenter.validate_row(row, data)

        self.assertEqual(len(data), 2)

        self.assert_data(data[0], 'default', 42)
        self.assert_data(data[1], 'default_2', 42)

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
