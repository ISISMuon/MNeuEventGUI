"""Tests for the histogram settings presenter."""
from MNeuEventLib import BatchData

from MNeuEventGUI.histogram_settings.presenter import HistSettingsPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from tests.data_paths import FILE


class HistogramSettingsPresenterTest(TestHelper):

    def setUp(self):
        self.presenter = HistSettingsPresenter()

    def test_display_width(self):
        """
        Test that the resolution is correctly displayed
        for valid settings.
        """
        output = self.presenter.display_width(0, 10, 2)
        self.assertEqual(output, "Resolution: 5000.00 ns")

        output = self.presenter.display_width(0, 1, 3)
        self.assertEqual(output, "Resolution: 333.33 ns")

    def test_display_width_invalid(self):
        """
        Test that no resolution is displayed if num_bins
        is zero or not entered.
        """
        for num_bins in [0, None]:
            output = self.presenter.display_width(0, 4, num_bins)
            self.assertEqual(output,
                             "Resolution: N/A (invalid number of bins)")


    def test_display_min_time(self):
        """
        Test that no resolution is displayed if min_time is incorrect.
        """
        output = self.presenter.display_width(None, 10, 2048)
        self.assertEqual(output,
                         "Resolution: N/A (invalid min time)")

    def test_display_max_time(self):
        """
        Test that no resolution is displayed if min_time is incorrect.
        """
        output = self.presenter.display_width(0, None, 2048)
        self.assertEqual(output,
                         "Resolution: N/A (invalid max time)")

    def test_display_bad_range(self):
        """
        Test that no resolution is displayed if min_time is incorrect.
        """
        for time_range in [(5, 3), (None, None)]:
            output = self.presenter.display_width(time_range[0],
                                                  time_range[1],
                                                  2048)
            self.assertEqual(output,
                             "Resolution: N/A (invalid time range)")


class HistogramSettingsPresenterBatchTest(TestHelper):
    """
    Check that the presenter only changes the
    settings for the active batch.
    """

    def setUp(self):
        self.presenter = HistSettingsPresenter()
        self.data = BatchData(FILE, 64, 2)
        self.presenter.set_data(self.data)

    def test_set_values(self):
        default = self.data._dict(0)['hist_settings']
        self.assertTrue(self.presenter.set_values(0.5, 15.22, 1024, 1))
        self.assertEqual(self.data._dict(1)['hist_settings'],
                         {'min_time': 500, 'max_time': 15220,
                          'n_bins': 1024})
        self.assertEqual(self.data._dict(0)['hist_settings'], default)

    def test_set_values_unchanged(self):
        # e.g. the widgets being filled from the data
        self.presenter.set_values(0.5, 15.22, 1024, 1)
        self.assertFalse(self.presenter.set_values(0.5, 15.22, 1024, 1))
        self.assertFalse(self.presenter.set_values(0, 32.768, 2048, 0))

    def test_set_values_no_data(self):
        presenter = HistSettingsPresenter()
        self.assertFalse(presenter.set_values(0.5, 15.22, 1024, 0))
