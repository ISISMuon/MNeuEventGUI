import unittest
from MuonDataLib.GUI.table.column import (TableColumns,
                                          ButtonColumn,
                                          NumericColumn)
from MuonDataLib.test_helpers.unit_test import TestHelper
from MuonDataLib.test_helpers.table_ref_data import (COL_GROUPS,
                                                     COLS,
                                                     EXPECTED_NUMERIC)
from MuonDataLib.test_helpers.table_ref_data import expected_col_dict


class TableColumnsTest(TestHelper):

    def test_init(self):
        for data in COL_GROUPS:
            with self.subTest(data=data):
                table = TableColumns(data, False)
                self.assertArrays(table.cols, data)

    def test_bad_input(self):
        bad_input = [[], COLS, [1, 2, 3], 'bob']
        for data in bad_input:
            with self.subTest(data=data):
                try:
                    _ = TableColumns(data, False)
                except ValueError:
                    pass
                    return
                self.fail(f'should not accept bad input {data}')

    def test_init_with_delete(self):
        """
        Once we know we can make a group with just a
        delete button, we dont need to explicitly test
        it anywhere else. It will behave like the other
        test cases.
        """
        for data in COL_GROUPS:
            with self.subTest(data=data):
                table = TableColumns(data, True, 'rm')

                # the delete button will add a table group
                self.assertArrays(table.cols[1:], data)

                # check only one table group
                del_btn = table.cols[0]
                self.assertEqual(len(del_btn.cols), 1)
                self.assertEqual(del_btn.name, None)
                # get list of columns
                del_btn = del_btn.cols
                self.assertEqual(len(del_btn), 1)
                # finally get the button
                del_btn = del_btn[0]
                self.assertEqual(del_btn.ID, 'Delete_rm')
                self.assertEqual(del_btn.name, '')
                assert isinstance(del_btn, ButtonColumn)

    def test_init_fail_add_delete(self):
        for data in COL_GROUPS:
            with self.subTest(data=data):
                try:
                    _ = TableColumns(data, True)
                except RuntimeError:
                    pass
                    return
                self.fail('Should throw an error if no ID')

    def test_init_fail_bad_input(self):
        bad = ['fail', [], COLS, [1, 2, 3]]
        for data in bad:
            with self.subTest(data=data):
                try:
                    _ = TableColumns(data, True)
                except RuntimeError:
                    pass
                    return
                self.fail('Should throw an error if no ID')

    def test_set_title(self):
        for data in COL_GROUPS:
            with self.subTest(data=data):
                table = TableColumns(data, False)
                titles = [group.name for group in table.cols]
                table.set_title(0, 'new')
                for k, name in enumerate(titles):
                    title_at_k = table.cols[k].name
                    expect = name
                    if k == 0:
                        expect = 'new'
                    self.assertEqual(title_at_k, expect)

    def test_set_title_index_1(self):
        for data in COL_GROUPS:
            with self.subTest(data=data):
                table = TableColumns(data, False)
                titles = [group.name for group in table.cols]
                try:
                    table.set_title(1, 'new')
                    for k, name in enumerate(titles):
                        title_at_k = table.cols[k].name
                        expect = name
                        if k == 1:
                            expect = 'new'
                        self.assertEqual(title_at_k, expect)

                except RuntimeError:
                    if len(titles) > 1:
                        self.fail("data exists, should be able to set")

    def test_set_range(self):
        for data, expected_numeric in zip(COL_GROUPS, EXPECTED_NUMERIC):
            with self.subTest(data=data):
                numeric_cols = 0
                table = TableColumns(data, False)
                table.set_range(1.2, 4.7)
                for group in table.cols:
                    for col in group.cols:
                        if isinstance(col, NumericColumn):
                            self.assertEqual(col._min, 1.2)
                            self.assertEqual(col._max, 4.7)
                            numeric_cols += 1
                self.assertEqual(numeric_cols, expected_numeric)

    def test_get_column_dict(self):
        names = ['test', 'more']
        IDs = ['Test', 'More']
        for data in COL_GROUPS:
            with self.subTest(data=data):
                table = TableColumns(data, False)
                col_dict = table.get_column_dict
                for j, group in enumerate(table.cols):
                    if len(group.cols) > 1:
                        self.assertEqual(col_dict[j]['headerName'], 'group')
                        for k, col in enumerate(group.cols):
                            self.assertEqual(col_dict[j]['headerName'],
                                             'group')
                            children = col_dict[j]['children']
                            self.assertEqual(children[k],
                                             expected_col_dict(type(col),
                                                               IDs[k],
                                                               names[k]))
                    else:
                        for col in group.cols:
                            self.assertEqual(col_dict[j],
                                             expected_col_dict(type(col),
                                                               'Unit',
                                                               'unit'))


if __name__ == '__main__':
    unittest.main()
