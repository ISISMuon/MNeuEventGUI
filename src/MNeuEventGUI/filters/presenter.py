from MNeuEventLib import _get_filter_times

from MNeuEventGUI.amp.presenter import AmpPresenter
from MNeuEventGUI.filters.view import FilterView
from MNeuEventGUI.histogram_settings.presenter import HistSettingsPresenter
from MNeuEventGUI.log.presenter import LOG_TABLE, LogPresenter
from MNeuEventGUI.presenter_template import PresenterTemplate
from MNeuEventGUI.time.presenter import TIME_TABLE, TimePresenter


class FilterPresenter(PresenterTemplate):
    """
    A class for the filter widget's presenter.
    This code follows the MVP template,
    note that the model is MNeuEventLib's BatchData class.
    """
    def __init__(self):
        """
        Create the presenter.
        Hold a copy of:
        - time filter table
        """
        self._time = TimePresenter()
        self._log = LogPresenter()
        self._amp = AmpPresenter()
        self._hist_settings = HistSettingsPresenter()
        self._view = FilterView(self)
        self._data = None
        self._time_file_data = []
        self._log_file_data = []
        self._amp_file_data = 0

    def show_file(self,
                  name,
                  time_data,
                  log_data,
                  amp_data,
                  min_time,
                  max_time,
                  num_bins):
        """
        If to display the name of the loaded
        filter file. This method chekcs
        the data currently in the table,
        so if you alter it and then change it
        back the file name will reappear.
        :param name: the name of the file
        :param time_data: the data from the
        time filter table
        :param log_data: the log data for the
        log filter table
        :param amp_data: The amplitude filter data
        :returns: if to hide the name in the GUI
        """
        hist_settings = self._data._dict(0)["hist_settings"]
        return not (self._time_file_data == time_data
            and self._log_file_data == log_data
            and self._amp_file_data == float(amp_data)
            and hist_settings["min_time"] == min_time
            and hist_settings["max_time"] == max_time
            and hist_settings["num_bins"] == num_bins)

    @property
    def headers(self):
        """
        Get the column headers
        :returns: the column headers (time table)
        """
        return self._time.cols.get_column_dict

    def set_data(self, data):
        """
        A method to set the muon data
        :param data: MNeuEventLib Data object
        """
        self._data = data
        self._time.set_data(data)
        self._log.set_data(data)
        times = self._data.dataset.get_frame_times() * 1e-9

        self._time.set_time_range(times[0], times[-1] + 32e-6)

    def read_filters(self) -> tuple:
        """
        Read the filter tables with the data from the Data object.
        """
        # todo: expand for batch processing
        data = self._data._dict(0)

        # note we convert min_time and max_time to microseconds
        return (data["time_filter_type"],
        self._time.load(data["time_filters"]),
        self._log.load(data["sample_log_filters"]),
        self._amp.load(data["amplitudes"]),
        data["hist_settings"]["min_time"] * 1e-3,
        data["hist_settings"]["max_time"] * 1e-3,
        data["hist_settings"]["n_bins"],
        self.headers,
        ""
        )

    def get_log_y_range(self, row_log):
        """
        Gets the min and max y values according to
        the sample log filter table. e.g. if an above
        filter it will give the threshold from the
        table and the maximum y value.
        :param row_log: a row from the log filter
        table
        :returns: the smallest and largest y values for
        the filter
        """
        # not quite sure why we're getting the log. but this was there before
        _ = self._data.dataset.get_sample_log(row_log['sample_log-table'])

        f_type = row_log['magic']
        if f_type == 'between':
            return row_log['y0_log-table'], row_log['yN_log-table']

        elif f_type == 'above':
            return row_log['y0_log-table'], row_log['y_max_log-table']

        elif f_type == 'below':
            return row_log['y_min_log-table'], row_log['yN_log-table']

        return row_log['y_min_log-table'], row_log['y_max_log-table']

    def calculate(self, n_clicks):
        """
        A method to calculate the number of
        events that would be used to make
        the histogram.
        :param n_clicks: the number of button
        presses for the calculate button
        :param time_filters: the list of time
        filters
        :param state: If to include or exclude the
        data.
        :param log_filters: the data from the
        sample log filter table
        :param amp_filter: the amplitude filter
        :returns: The string to display the number
        of events, the error message (if there is one)
        :param min_time: the minimum time for the histogram
        :param max_time: the maximum time for the histogram
        :param num_bins: the number of bins for the histogram
        """
        _ = self._data.calculate()
        N = f"{self._data.get_n_events(0)[0]:,}"
        return self._view.get_N(N), ''

    def load(self, filters: dict):
        """
        Loads the filters that have been reported from a Filters json.
        :param filters: the JSON filter data
        :returns: the time filters, the sample log
        filters, the amplitude filters, if to include/exclude the time filters,
        and the table headers
        """
        state = filters["time_filter_type"]
        time_data = self._time.load(filters["time_filters"])
        self._time_file_data = time_data
        self._time.set_state(state)

        log_data = self._log.load(filters["sample_log_filters"])
        self._log_file_data = log_data

        self._amp_file_data = self._amp.load(filters["amplitudes"])

        print('loading filters ....')
        return (time_data, log_data, self._amp_file_data, state, self.headers)

    def update_N_events(self, update: list[dict], current_str: str) -> str:
        """
        Update the events string when the filters are updated.
        Expects update data in the form returned by
        the Dash cellValueChanged property.
        :param update: The filter update data.
        :param current_str: The current string for the number of events.
        :returns: The string to display for the number of events.
        """
        # I'm not sure if it's even possible
        # to update multiple cells simultaneously
        # but we have to unwrap this list anyway
        # so may as well do it properly
        for updated_cell in update:
            col = updated_cell.get('colId', None)

            # if a filter value has changed, we need to clear the string
            # but we don't if just e.g. name changed
            update_required = col in ['Start_' + TIME_TABLE,
                                      'End_' + TIME_TABLE,
                                      'filter_' + LOG_TABLE,
                                      'y0_' + LOG_TABLE,
                                      'yN_' + LOG_TABLE,
                                      ]

            if update_required:
                return self._view.no_events_str

        return current_str

