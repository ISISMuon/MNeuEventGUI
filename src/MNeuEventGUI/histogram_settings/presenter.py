from MuonDataLib.GUI.presenter_template import PresenterTemplate
from MuonDataLib.GUI.histogram_settings.view import HistSettingsView


class HistSettingsPresenter(PresenterTemplate):
    """
    A class for the presenter of the histogram settings widget.
    """

    def __init__(self):
        self._view = HistSettingsView(self)

    def display_width(self, min_time, max_time, num_bins):
        """
        Calculate bin width of a histogram from a range and number of bins.
        :param min_time: The lower limit of the range.
        :param max_time: The upper limit of the range.
        :param num_bins: The number of bins.
        :returns: The width of each bin.
        """
        err_msg = None
        if self.check_num_bins_invalid(num_bins):
            err_msg = "invalid number of bins"

        invalid_range = self.check_range_invalid(min_time, max_time)
        if all(invalid_range):
            err_msg = "invalid time range"
        elif invalid_range[0]:
            err_msg = "invalid min time"
        elif invalid_range[1]:
            err_msg = "invalid max time"

        if err_msg is not None:
            return f"Resolution: N/A ({err_msg})"

         # 1e3 is the conversion from micro to nano seconds
        width = ((max_time - min_time) * 1e3) / num_bins

        return f"Resolution: {width:.2f} ns"

    def check_num_bins_invalid(self, num_bins: int) -> bool:
        """
        Check whether the number of bins is valid.
        :input num_bins: The number of bins.
        :returns: Whether the number of bins is valid.
        """
        return num_bins is None or num_bins <= 0

    def check_range_invalid(self, min_time: float, max_time: float) -> bool:
        """
        Check whether the minimum and maximum times are valid.
        :input min_time: The minimum time value.
        :input max_time: The maximum time value.
        :returns: A pair of bools: the first is True if min_time is invalid,
                  the second is True if max_time is invalid.
        """
        invalid = (min_time is None, max_time is None)
        if not any(invalid):
            if min_time > max_time:
                return (True, True)
        return invalid
