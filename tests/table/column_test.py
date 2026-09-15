import unittest
from MuonDataLib.GUI.table.column import ButtonColumn, NumericColumn
from MuonDataLib.test_helpers.unit_test import TestHelper
from MuonDataLib.test_helpers.table_ref_data import VALID_DTYPES as VALID
from MuonDataLib.test_helpers.table_ref_data import expected_col_dict


class ColumnTest(TestHelper):

    def test_set_icon(self):
        col = ButtonColumn('unit', 'test')
        self.assertEqual(col._icon, 'bi bi-trash me-2')
        self.assertEqual(col._className, 'btn btn-danger')

        col.set_icon('tick', 'primary')
        self.assertEqual(col._icon, 'tick')
        self.assertEqual(col._className, 'primary')

        data = col.get_column_dict
        self.assertEqual(data['cellRendererParams']['Icon'],
                         'tick')
        self.assertEqual(data['cellRendererParams']['className'],
                         'primary')

    def test_set_uneditable(self):
        for dtype in VALID:
            with self.subTest(dtype=dtype):
                col = dtype('unit', 'test')
                data = col.get_column_dict
                self.assertEqual(data['editable'],
                                 not isinstance(col, ButtonColumn))

                col.set_uneditable()
                data = col.get_column_dict
                self.assertEqual(data['editable'], False)

    def test_set_range(self):
        col = NumericColumn('unit', 'test')
        col.set_range(1.2, 4.7)

        self.assertEqual(col._min, 1.2)
        self.assertEqual(col._max, 4.7)

    def test_get_column_dict(self):
        for dtype in VALID:
            with self.subTest(dtype=dtype):
                col = dtype('unit', 'test')
                col_dict = col.get_column_dict
                self.assertEqual(col_dict,
                                 expected_col_dict(dtype))


if __name__ == '__main__':
    unittest.main()
