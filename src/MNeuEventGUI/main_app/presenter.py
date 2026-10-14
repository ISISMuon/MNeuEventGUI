from dash import no_update

from MNeuEventGUI.control_pane.presenter import ControlPanePresenter
from MNeuEventGUI.load_bar.presenter import LoadBarPresenter
from MNeuEventGUI.save_bar.presenter import SaveBarPresenter


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

    def confirm_load(self, n_clicks, data, submit):
        """
        Gives a confirm pop up iff filters are presnt.
        If the pop up is not shown we still increment
        the number of submit clicks for the pop-up,
        because we still want to trigger the
        events.
        :param n_clicks: Number of clicks of load
        :param data: the time filter table data
        :param submit: the number of clicks of submit
        :reuturn: if to show the confirm pop=-p and the number
        of submit clicks.
        """
        if len(data) > 0:
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

    def load_filter(self, name):
        """
        Loads a filter file into the GUI.
        :param name: The name of the filter file
        :returns: the table data for each part of the GUI:
          - time data;
          - log data;
          - amplitude;
          - state;
          - histogram minimum time;
          - histogram maximum time;
          - histogram number of bins;
          - table headers.
        """
        return self.control.read_filter(name)


    def alert(self, text):
        """
        Opens the alert if new information
        has been uploaded.
        :param text: the text to be displayed in
        the alert.
        :returns: if to open the alert
        """
        return text != ''

    def save_data(self, name):
        """
        Saves either a muon histogram nexus file
        or a filter file, from the current muon
        event data.
        :param name: a string of the data type (json
        or nexus) and the name of the file to save to.
        :param time_filters: the time filters (list of dicts) to use
        :param time_mode: If the time filters are to include
        or exclude the data
        :param log_filters: the data from the sample log
        filter table
        :param amp_filters: the amplitude filters
        :param min_time: the histogram minimum time
        :param max_time: the histogram maximum time
        :param num_bin: the number of histogram bins
        :param debug: if debug mode is on or off.
        :returns: the name of the saved file and
        the alert message
        """
        data = self.load.get_data
        if 'None' in name:
            return '', ''
        dtype = name[0]
        file = name[1:]

        print("saving to ", file)
        if dtype == "n":
            print(file)
            data.save(0, file)
        elif dtype == 'j':
            data.save_filters(0, file)
        return file, ''


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
        histogram
        :param data: the amplitude filter data
        :returns: the plot object
        """
        return self.control._filter._amp.plot(data)

    def load_nxs(self, name, time_data,
                 log_data, debug_state):
        """
        Loads a muon event nexus file.
        :param name: the name of the file to open.
        :param time_data: the time filter table data
        :param log_data: the log filter table data
        :param debug_state: if debug mode is on or off.
        :returns: yields:
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
        - the alert message
        - the number of events string
        """
        if name == self.load.file:
            # same file, so the data (and the number of
            # events) is unchanged and only the settings
            # are read back
            (_, _, amp, state,
             min_time, max_time,
             num_bins, headers) = self.control.refresh()
            return (self.control._plot.fig,
                    time_data, False,
                    log_data, False,
                    amp, state, min_time, max_time, num_bins,
                    headers,
                    self.control._filter._amp._plot.fig,
                    '',
                    no_update)
        self.load.set_file(name)

        # any previous number of events was for the old data
        no_events = self.control.no_events_str

        if 'None' in name:
            # there is no data to read the settings from
            return (self.plot(),
                    [],
                    True,
                    [],
                    True,
                    no_update, no_update, no_update, no_update, no_update,
                    self.control.headers,
                    {},
                    '',
                    no_events)

        self.load.load_nxs(name)

        data = self.load.get_data
        self.control.set_data(data)

        (times, logs, amp, state,
         min_time, max_time,
         num_bins, headers) = self.control.refresh()

        return (self.plot(), times, False, logs, False,
                amp, state, min_time, max_time, num_bins,
                headers, self.plot_amps(data), '',
                no_events)
