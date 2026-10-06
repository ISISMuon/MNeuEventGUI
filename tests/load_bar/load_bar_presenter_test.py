import unittest
from unittest import mock
from MNeuEventLib import BatchData
from MNeuEventGUI.load_bar.presenter import LoadBarPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE  # noqa: E402


class LoadBarPresenterTest(TestHelper):

    @mock.patch("MNeuEventGUI.load_bar.presenter.LoadBarView")
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

        self.assertIsInstance(self.load._data, BatchData)
        # check it is the test file
        self.assertEqual(self.load._data.dataset.sample_log_names,
                         ['B', 'I', 'Temp'])
        self.load._data.calculate()
        self.assertEqual(self.load._data.get_n_events(0), [64147])

    @mock.patch("MNeuEventGUI.load_bar.presenter.BatchData")
    def test_get_data(self, data_mock):
        data_mock.return_value = mock.Mock()
        self.load.load_nxs(FILE)
        data_mock.assert_called_once_with(FILE, 64, 1)
        self.assertEqual(self.load._data, data_mock())
        self.assertEqual(self.load.get_data, data_mock())

    def test_set_file(self):
        self.assertEqual(self.load.name, '')
        self.load.set_file("test.nxs")
        self.assertEqual(self.load.name, 'test.nxs')

    def test_file(self):
        self.load.set_file("test.nxs")
        self.assertEqual(self.load.file, 'test.nxs')


if __name__ == '__main__':
    unittest.main()
