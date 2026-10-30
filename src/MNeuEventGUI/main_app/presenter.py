from dash import no_update

from MNeuEventGUI.control_pane.presenter import ControlPanePresenter
from MNeuEventGUI.load_bar.presenter import LoadBarPresenter
from MNeuEventGUI.save_bar.presenter import SaveBarPresenter
from MNeuEventGUI.utils.batch import active_batch, per_batch
from MNeuEventGUI.utils.errors import GUIError


class MainAppPresenter:

    def __init__(self, open_nxs_func):
        """
        This is the presenter for the
        main app. It follows the MVP
        pattern, but the view
        is the main app.
        :param open_nxs_func: the function for
        opening a nxs file
        """
        self.load = LoadBarPresenter()
        self.control = ControlPanePresenter()
        self.save = SaveBarPresenter()
        self._open_nxs_func = open_nxs_func
        self.N_submit = 0

    def open_nxs(self, n_clicks, name):
        """
        A method to open a nexus file.
        If the filters are empty it
        skips the confirm dialog.
        :param n_clicks: number of times submit
        has been pressed
        :param name: the name of the current file
        :returns: the name of the "new file"
        """
        if n_clicks > self.N_submit:
            self.N_submit += 1
            return self._open_nxs_func(self.N_submit)
        return name

    def confirm_load(self, n_clicks, time_data, log_data, submit):
        """
        Gives a confirm pop up iff any batch has filters.
        If the pop up is not shown we still increment
        the number of submit clicks for the pop-up,
        because we still want to trigger the
        events.
        :param n_clicks: Number of clicks of load
        :param time_data: the time filter table data for each batch
        :param log_data: the log filter table data for each batch
        :param submit: the number of clicks of submit
        :reuturn: if to show the confirm pop=-p and the number
        of submit clicks.
        """
        if any(len(table) > 0 for table in time_data + log_data):
            return True, submit
        return False, submit + 1

    def debug(self, state):
        """
        This prints a notifcation that the debug mode
        is on. This will not be a long term feature
        and is here for testing. Debug mode just
        casues all of the methods to throw errors.
        :param state: if debug mode is on or off (bool)
        """
        tmp = 'off'
        if state:
            tmp = 'on'

        print("debug mode " + tmp)


    def save_data(self, name, active_tab):
        """
        Saves either a muon histogram nexus file
        for each batch, or a filter file for the
        active batch, from the current muon
        event data.
        :param name: a string of the data type (json
        or nexus) and the name of the file to save to.
        :param active_tab: the ID of the active batch tab
        :returns: the name of the saved file
        :raises GUIError: if the data cannot be saved
        """
        data = self.load.get_data
        if 'None' in name:
            return ''
        dtype = name[0]
        file = name[1:]

        print("saving to ", file)
        try:
            if dtype == "n":
                # a separate file for each batch
                data.save('all', file, nexus_v3=False)
            elif dtype == 'j':
                data.save_filters(active_batch(active_tab), file)
        except Exception as error:
            raise GUIError(f'The data could not be '
                           f'saved to {file}.') from error
        return file

    def plot(self):
        """
        A method to plot the sample log data.
        This exists to make some code cleaner
        :returns: the plot object
        """
        return self.control.plot_default()

    def plot_amps(self, data):
        """
        Simple method to plot the amplitude
        histogram for each batch
        :param data: the amplitude filter data
        :returns: the plot object for each batch
        """
        return [filter_presenter._amp.plot(data)
                for filter_presenter in self.control._filters]

    def load_nxs(self, name, time_data,
                 log_data, debug_state):
        """
        Loads a muon event nexus file.
        Apart from the plot,
        the values are a list with a value for each batch.
        :param name: the name of the file to open.
        :param time_data: the time filter table data
        :param log_data: the log filter table data
        :param debug_state: if debug mode is on or off.
        :returns: a tuple containing:
        - the updated figure
        - the time filter table data
        - if the time filter table is disabled
        - the sample log table data
        - if the sample log table is disabled
        - the amplitude filter
        - if to include/exclude the time filters
        - the histogram's minimum time
        - the histogram's maximum time
        - the histogram's number of bins
        - the filter table column names
        - plot of the amplitude histogram
        - the number of events string
        :raises GUIError: if the file cannot be read
        """
        if not name or 'None' in name:
            # there is no file, because the file browser was cancelled
            # or because a failed load has put the name back to there
            # being no file (see the except below). The same file check
            # cannot be used, as there is no data to read settings from.
            self.load.set_file(name)
            return (self.plot(),
                    per_batch([]),
                    per_batch(True),
                    per_batch([]),
                    per_batch(True),
                    *[per_batch(no_update)] * 5,
                    self.control.headers,
                    per_batch({}),
                    per_batch(self.control.no_events_str))

        if name == self.load.file:
            # same file, so the data (and the number of
            # events) is unchanged and only the settings
            # are read back
            (_, _, amp, state,
             min_time, max_time,
             num_bins, headers) = self.control.refresh()
            return (self.control._plot.fig,
                    time_data, per_batch(False),
                    log_data, per_batch(False),
                    amp, state, min_time, max_time, num_bins,
                    headers,
                    [filter_presenter._amp._plot.fig
                     for filter_presenter in self.control._filters],
                    per_batch(no_update))
        previous = self.load.file
        self.load.set_file(name)

        # any previous number of events was for the old data
        no_events = per_batch(self.control.no_events_str)

        try:
            self.load.load_nxs(name)
            data = self.load.get_data
            self.control.set_data(data)
        except Exception as error:
            # the load bar names the file that is loaded, so a file
            # that failed has to be taken back off of it
            self.load.set_file(previous)
            raise GUIError(f'The file {name} '
                           f'could not be loaded.',
                           {'file_name': {'children': previous}}) from error

        (times, logs, amp, state,
         min_time, max_time,
         num_bins, headers) = self.control.refresh()

        return (self.plot(), times, per_batch(False), logs, per_batch(False),
                amp, state, min_time, max_time, num_bins,
                headers, self.plot_amps(data),
                no_events)
