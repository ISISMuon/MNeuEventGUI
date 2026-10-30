import unittest

from MNeuEventLib import BatchData

from MNeuEventGUI.amp.presenter import BASELINE, AmpPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from tests.data_paths import FILE


class AmpPresenterBatchTest(TestHelper):
    """
    Check that the presenter only changes the
    amplitude filter for its own batch.
    """

    def setUp(self):
        self.presenter = AmpPresenter(batch=1)
        self.data = BatchData(FILE, 64, 2)
        self.presenter.set_data(self.data)

    def test_batch(self):
        self.assertEqual(self.presenter.batch, 1)
        self.assertEqual(self.presenter._plot.batch, 1)

    def test_edit_baseline(self):
        self.presenter.edit_baseline(2.7)
        amps = self.data._dict(1)['amplitudes']
        self.assertEqual(self.presenter.load(amps), 2.7)
        self.assertNotIn(str(BASELINE), self.data._dict(0)['amplitudes'])


if __name__ == '__main__':
    unittest.main()
