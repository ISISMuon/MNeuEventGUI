import unittest

from MNeuEventLib import BatchData

from MNeuEventGUI.amp.presenter import BASELINE, AmpPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from tests.data_paths import FILE


class AmpPresenterBatchTest(TestHelper):
    """
    Check that the presenter only changes the
    amplitude filter for the active batch.
    """

    def setUp(self):
        self.presenter = AmpPresenter()
        self.data = BatchData(FILE, 64, 2)
        self.presenter.set_data(self.data)

    def test_edit_baseline(self):
        self.assertTrue(self.presenter.edit_baseline(2.7, 1))
        amps = self.data._dict(1)['amplitudes']
        self.assertEqual(self.presenter.load(amps), 2.7)
        self.assertNotIn(str(BASELINE), self.data._dict(0)['amplitudes'])

    def test_edit_baseline_unchanged(self):
        # e.g. the widget being filled from the data
        self.presenter.edit_baseline(2.7, 1)
        self.assertFalse(self.presenter.edit_baseline('2.7', 1))
        self.assertFalse(self.presenter.edit_baseline(0, 0))

    def test_edit_baseline_empty(self):
        self.assertFalse(self.presenter.edit_baseline(None, 0))
        self.assertFalse(self.presenter.edit_baseline('', 0))

    def test_edit_baseline_no_data(self):
        presenter = AmpPresenter()
        self.assertFalse(presenter.edit_baseline(2.7, 0))


if __name__ == '__main__':
    unittest.main()
