from dash import no_update
from dash.exceptions import PreventUpdate

from MNeuEventGUI.amp.presenter import AmpPresenter
from MNeuEventGUI.filters.view import FilterView
from MNeuEventGUI.histogram_settings.presenter import HistSettingsPresenter
from MNeuEventGUI.log.presenter import LOG_TABLE, LogPresenter
from MNeuEventGUI.presenter_template import PresenterTemplate
from MNeuEventGUI.time.presenter import TIME_TABLE, TimePresenter
from MNeuEventGUI.utils.batch import INITIAL_BATCHES
from MNeuEventGUI.utils.errors import GUIError


def new_batch_state():
    """
    :returns: the state of the widgets for a new batch
    that is not kept in the data
    """
    # file: the name of the loaded filter file ('' if none),
    # time/log/amp: the filters the file had, so we know if
    # the batch still matches it,
    # n_events: the number of events when it was last calculated
    # (None if the filters have changed since). This is kept
    # because the data's results are reset when any batch changes.
    return {'file': '', 'time': [], 'log': [], 'amp': 0,
            'n_events': None}


class FilterPresenter(PresenterTemplate):
    """
    A class for the filter widget's presenter.
    This code follows the MVP template,
    note that the model is MNeuEventLib's BatchData class.

    The widgets are shared by all of the batches and show
    the active batch, so the callbacks are given the index
    of the active batch (see utils/batch.py).
    """
    def __init__(self, num_batches=INITIAL_BATCHES):
        """
        Create the presenter.
        :param num_batches: the number of batches to start with
        """
        self._time = TimePresenter()
        self._log = LogPresenter()
        self._amp = AmpPresenter()
        self._hist_settings = HistSettingsPresenter()
        self._view = FilterView(self)
        self._data = None
        self._batches = [new_batch_state() for _ in range(num_batches)]

    def add_batch(self):
        """
        Adds the widget state for a new batch, after
        the existing ones.
        """
        self._batches.append(new_batch_state())

    def remove_batch(self, index):
        """
        Removes the widget state for a batch.
        :param index: the index of the batch
        """
        del self._batches[index]

    def show_file(self,
                  name,
                  time_data,
                  log_data,
                  amp_data,
                  min_time,
                  max_time,
                  num_bins,
                  batch):
        """
        If to display the name of the loaded
        filter file. This method checks
        the data currently in the table,
        so if you alter it and then change it
        back the file name will reappear.
        :param name: the name of the file
        :param time_data: the data from the
        time filter table
        :param log_data: the log data for the
        log filter table
        :param amp_data: The amplitude filter data
        :param min_time: the histogram's minimum time
        :param max_time: the histogram's maximum time
        :param num_bins: the histogram's number of bins
        :param batch: the index of the active batch
        :returns: if to hide the name in the GUI
        """
        if self._data is None or not name:
            return True

        state = self._batches[batch]
        hist_settings = self._data._dict(batch)["hist_settings"]
        # the data stores times in ns, the GUI uses microseconds
        return not (state['time'] == time_data
            and state['log'] == log_data
            and amp_data is not None and amp_data != ''
            and state['amp'] == float(amp_data)
            and hist_settings["min_time"] / 1e3 == min_time
            and hist_settings["max_time"] / 1e3 == max_time
            and hist_settings["n_bins"] == num_bins)

    @property
    def headers(self):
        """
        Get the column headers
        :returns: the column headers (time table)
        """
        return self._time.cols.get_column_dict

    @property
    def no_events_str(self):
        """
        Get the string for when the number of events
        has not been calculated.
        :returns: the string for no events
        """
        return self._view.no_events_str

    def n_events_text(self, batch):
        """
        Gets the number of events for a batch, if it
        is up to date.
        :param batch: the index of the batch
        :returns: the number of events component
        """
        n_events = self._batches[batch]['n_events']
        return self.no_events_str if n_events is None else n_events

    def uncount(self, batch):
        """
        Marks a batch's number of events as out of date,
        because its filters have changed.
        :param batch: the index of the batch
        :returns: the string for no events
        """
        self._batches[batch]['n_events'] = None
        return self.no_events_str

    def fill(self, active, num_batches=None):
        """
        Gets the values for the widgets when the active
        batch changes (or a batch is added or removed).
        :param active: the index of the active batch
        :param num_batches: the number of batches (only
        used so this is updated when it changes)
        :returns: the values for the filters and settings
        (see values), the name of the batch's filter file
        and the number of events
        :raises PreventUpdate: if there is no data
        """
        if self._data is None:
            raise PreventUpdate
        return (*self.values(active),
                self._batches[active]['file'],
                self.n_events_text(active))

    def set_data(self, data):
        """
        A method to set the muon data
        :param data: MNeuEventLib Data object
        """
        self._data = data
        self._time.set_data(data)
        self._log.set_data(data)
        self._amp.set_data(data)
        self._hist_settings.set_data(data)
        # the numbers of events were for the old data
        for batch in range(len(self._batches)):
            self.uncount(batch)

    def clear(self):
        """
        Clears the stored data when a bad file is
        loaded.
        """
        self._data = None
        self._time.data = None
        self._log.data = None
        self._amp.data = None
        self._hist_settings.data = None

    def values(self, batch) -> tuple:
        """
        Get the GUI values for a batch's filters and
        settings, from the Data object.
        :param batch: the index of the batch
        :returns: the time filters, the sample log filters,
        the amplitude filter, if to include/exclude the time
        filters, the histogram settings (minimum time, maximum
        time and number of bins) and the table headers
        """
        filters = self._data._dict(batch)
        state = filters["time_filter_type"]
        time_data = self._time.load(filters["time_filters"])
        self._time.show_state(state)

        log_data = self._log.load(filters["sample_log_filters"])
        amp_data = self._amp.load(filters["amplitudes"])

        min_time, max_time, num_bins = self._hist_settings.load(
            filters["hist_settings"])

        return (time_data, log_data, amp_data, state,
                min_time, max_time, num_bins, self.headers)

    def has_filters(self):
        """
        :returns: if any batch has a time or sample log filter
        """
        if self._data is None:
            return False
        for batch in range(len(self._batches)):
            filters = self._data._dict(batch)
            if filters['time_filters'] or filters['sample_log_filters']:
                return True
        return False

    def edit_amp(self, value, batch):
        """
        Sets the amplitude baseline for a batch.
        :param value: the amplitude baseline
        :param batch: the index of the active batch
        :returns: the number of events string, which is
        cleared if the baseline changed
        """
        if self._amp.edit_baseline(value, batch):
            return self.uncount(batch)
        return no_update

    def edit_hist_settings(self, min_time, max_time, num_bins, batch):
        """
        Sets the histogram settings for a batch.
        :param min_time: the histogram's minimum time
        :param max_time: the histogram's maximum time
        :param num_bins: the histogram's number of bins
        :param batch: the index of the active batch
        :returns: the number of events string, which is
        cleared if the settings changed
        """
        if self._hist_settings.set_values(min_time, max_time,
                                          num_bins, batch):
            return self.uncount(batch)
        return no_update

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

    def n_events(self, batch):
        """
        Gets the GUI component for the number of
        events in the calculated histogram for
        a batch.
        :param batch: the index of the batch
        :returns: the number of events component
        """
        N = f"{self._data.get_n_events(batch)[0]:,}"
        return self._view.get_N(N)

    def calculate(self, n_clicks, batch):
        """
        A method to calculate the number of
        events that would be used to make
        the histogram for each batch.
        :param n_clicks: the number of clicks of the
        calculate button
        :param batch: the index of the active batch
        :returns: The number of events to display
        for the active batch
        :raises GUIError: if no data is loaded
        :raises RuntimeError: if the filters cannot be applied
        """
        if self._data is None:
            raise GUIError('Please load a file before calculating.')
        self._data.calculate()
        for index, state in enumerate(self._batches):
            state['n_events'] = self.n_events(index)
        return self.n_events_text(batch)

    def load_filter_file(self, name, batch):
        """
        Loads the filters from a file into
        the active batch.
        :param name: the name of the json file
        :param batch: the index of the active batch
        :returns: the values for the filters and settings
        (see values), the name of the file and the
        number of events
        :raises GUIError: if the filter file cannot be read
        """
        if not name or name == 'None':
            return (no_update,) * 10
        try:
            self._data.load_filters(batch, name)
            values = self.values(batch)
        except Exception as error:
            raise GUIError(f'The filter file {name} '
                           f'could not be loaded.') from error

        # record the file's values, so we know if the GUI
        # still matches the file that was loaded
        state = self._batches[batch]
        state['file'] = name
        state['time'], state['log'], state['amp'] = values[:3]
        print('loading filters ....')
        return (*values, name, self.uncount(batch))

    def update_N_events(self, update: list[dict], current_str: str,
                        batch) -> str:
        """
        Update the events string when the filters are updated.
        Expects update data in the form returned by
        the Dash cellValueChanged property.
        :param update: The filter update data.
        :param current_str: The current string for the number of events.
        :param batch: the index of the active batch
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
                return self.uncount(batch)

        return current_str

