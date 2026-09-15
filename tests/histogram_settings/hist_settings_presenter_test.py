"""Tests for the histogram settings presenter."""
from MuonDataLib.GUI.histogram_settings.presenter import HistSettingsPresenter
from MuonDataLib.test_helpers.unit_test import TestHelper

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
