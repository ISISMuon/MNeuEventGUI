import unittest
from unittest import mock
from MNeuEventGUI.save_bar.presenter import SaveBarPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper


class SaveBarPresenterTest(TestHelper):

    @mock.patch("MNeuEventGUI.save_bar.presenter.SaveBarView")
    def setUp(self, view):
        self.view = view
        self.view.return_value = mock.Mock()
        self.save = SaveBarPresenter()

    def test_init(self):
        self.assertEqual(self.save._view,
                         self.view())


if __name__ == '__main__':
    unittest.main()
