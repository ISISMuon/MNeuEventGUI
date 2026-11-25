from MNeuEventGUI.histogram_settings.view import HistSettingsView
from MNeuEventGUI.presenter_template import PresenterTemplate


class HistSettingsPresenter(PresenterTemplate):
    """
    A class for the presenter of the histogram settings widget.
    """

    def __init__(self):
        """
        Create the presenter.
        """
        self._view = HistSettingsView(self)
        self.data = None

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

    def set_data(self, data):
        """
        Set the data model for this presenter.
        """
        self.data = data

    def set_values(self, min_time, max_time, num_bins, batch):
        """
        Set the histogram settings in the data to some
        values, if they are different to the batch's
        current settings.
        :param min_time: the start time for the histogram
        :param max_time: the end time for the histogram
        :param num_bins: the number of bins in the histogram
        :param batch: the index of the active batch
        :returns: if the settings were changed
        """
        if self.data is None:
            return False
        current = self.data._dict(batch)['hist_settings']
        # the data stores whole ns, the GUI uses microseconds
        if (min_time is not None and max_time is not None
                and round(min_time * 1e3) == current['min_time']
                and round(max_time * 1e3) == current['max_time']
                and num_bins == current['n_bins']):
            return False
        self.data.set_histogram_settings(batch,
                                         min_time,
                                         max_time,
                                         num_bins)
        return True

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
        if not any(invalid) and min_time > max_time:
            return (True, True)
        return invalid

    def load(self, settings: dict) -> (float, float, int):
        """
        Load the histogram settings from a data dictionary.
        :param settings: The dictionary to get the settings from.
        :returns: The histogram settings.
        """
        # the data stores times in ns, the GUI uses microseconds
        return (settings["min_time"] / 1e3,
                settings["max_time"] / 1e3,
                settings["n_bins"])

