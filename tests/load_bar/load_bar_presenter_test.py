import unittest
from unittest import mock
from MuonDataLib.GUI.load_bar.presenter import LoadBarPresenter
from MuonDataLib.test_helpers.unit_test import TestHelper
import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE  # noqa: E402


class LoadBarPresenterTest(TestHelper):

    @mock.patch("MuonDataLib.GUI.load_bar.presenter.LoadBarView")
    def setUp(self, view):
        self.view = view
        self.view.return_value = mock.Mock()
        self.load = LoadBarPresenter()

    def test_init(self):
        self.assertEqual(self.load._view,
                         self.view())
        # Check that the data is none
        self.assertEqual(self.load._data,
                         None)

    def test_load_nxs(self):
        self.load.load_nxs(FILE)

        self.assertEqual(self.load._data._dict['raw_data']._dict['run_number'],
                         195790)

    @mock.patch("MuonDataLib.GUI.load_bar.presenter.load_events")
    def test_get_data(self, data_mock):
        data_mock.return_value = mock.Mock()
        self.load.load_nxs(FILE)
        self.assertEqual(self.load._data, data_mock())

    def test_set_file(self):
        self.assertEqual(self.load.name, '')
        self.load.set_file("test.nxs")
        self.assertEqual(self.load.name, 'test.nxs')

    def test_file(self):
        self.load.set_file("test.nxs")
        self.assertEqual(self.load.file, 'test.nxs')


if __name__ == '__main__':
    unittest.main()
