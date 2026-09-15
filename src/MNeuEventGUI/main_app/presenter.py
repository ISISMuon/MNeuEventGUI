from MuonDataLib.GUI.load_bar.view import CURRENT
from MuonDataLib.GUI.load_bar.presenter import LoadBarPresenter
from MuonDataLib.GUI.control_pane.presenter import ControlPanePresenter
from MuonDataLib.GUI.save_bar.presenter import SaveBarPresenter

from MuonDataLib.data.utils import create_data_from_function
import numpy as np


def osc(x, A, omega, phi):
    return A*np.sin(omega*x + phi)


class MainAppPresenter(object):

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

    def load_filter(self, name, debug):
        """
        Loads a filter file into the GUI
        and applies it to the muon
        event data.
        :param name: The name of the filter file
        :param debug: If debug mode is on or off
        :returns: The list of rows for the time filter table,
        the list of rows for the sample log filter table,
        the amplitude filter,
        the state of the time filters (include/exclude),
        the column headers
        and an error message (if it fails)
        """
        try:
            if debug:
                raise RuntimeError("Filter error")

            filters = name[len(CURRENT):]
            result = self.control.read_filter(filters)
            return (*result, '')
        except Exception as err:
            cols = self.control.headers
            return ([], [], 0, 0, 0, 0, 'Exclude',
                    cols, f'Load filter error: {err}')

    def alert(self, text):
        """
        Opens the alert if new information
        has been uploaded.
        :param text: the text to be displayed in
        the alert.
        :returns: if to open the alert
        """
        if text == '':
            return False
        return True

    def save_data(self, name, time_filters, time_mode,
                  log_filters, amp_filters,
                  min_time, max_time, num_bin, debug):
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
        try:
            if debug:
                raise RuntimeError("Saving error")

            hist_settings = (min_time, max_time, num_bin)

            print("saving to ", file)
            self.control._filter.apply_filters(time_filters,
                                               time_mode,
                                               log_filters,
                                               amp_filters,
                                               hist_settings)
            if dtype == "n":
                data.save_histograms(file)
            elif dtype == 'j':
                data.save_filters(file)
            return file, ''
        except Exception as err:
            return '', f'Saving Error: {err}'

    def gen_fake_data(self, data):
        """
        This creates fake data for the sample log.
        It will not be present long term.
        We assume one data point per second.
        :param data: the muon event data object
        :returns: the fake data
        """
        frame_start_times = data.get_frame_start_times()
        start = frame_start_times[0]
        end = frame_start_times[-1] + 1
        # 1 days worth of logs at 1 per second
        N = 60*60*24
        step = (end - start)/N
        return create_data_from_function(start, end,
                                         step,
                                         [3, 6.1, 0.91],
                                         osc, seed=1)

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
        :param name: the 'CURRENT' text string and
        the name of the file to open.
        :param time_data: the time filter table data
        :param log_data: the log filter table data
        :param debug_state: if debug mode is on or off.
        :returns: yields:
        - the updated figure
        - the time filter table data
        - if the time filter table is disabled
        - the sample log table data
        - if the sample log table is disabled
        - the filter table column names
        - plot of the amplitude histogram
        - the alert message
        """
        if name == self.load.file:
            # same file
            return (self.control._plot.fig,
                    time_data, False,
                    log_data, False,
                    self.control.headers,
                    self.control._filter._amp._plot.fig,
                    '')
        self.load.set_file(name)

        if 'None' in name:
            return (self.plot(),
                    [],
                    True,
                    [],
                    True,
                    self.control.headers,
                    {},
                    '')
        try:
            if debug_state:
                raise RuntimeError("Loading error")

            self.load.load_nxs(name[len(CURRENT):])

        except Exception as err:
            self.control.clear()
            return (self.plot(),
                    [],
                    True,
                    [],
                    True,
                    self.control.headers,
                    {},
                    f'An error occurred: {err}')

        data = self.load.get_data
        self.control.set_data(data)

        return (self.plot(), [], False, [], False,
                self.control.headers, self.plot_amps(data), '')
