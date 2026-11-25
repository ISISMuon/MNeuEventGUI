from dash import no_update

from MNeuEventGUI.control_pane.presenter import ControlPanePresenter
from MNeuEventGUI.load_bar.presenter import LoadBarPresenter
from MNeuEventGUI.save_bar.presenter import SaveBarPresenter
from MNeuEventGUI.utils.batch import INITIAL_BATCHES, batch_file_names
from MNeuEventGUI.utils.errors import GUIError


class MainAppPresenter:

    def __init__(self, open_nxs_func, num_batches=INITIAL_BATCHES):
        """
        This is the presenter for the
        main app. It follows the MVP
        pattern, but the view
        is the main app.
        :param open_nxs_func: the function for
        opening a nxs file
        :param num_batches: the number of batches to start with
        """
        self.load = LoadBarPresenter()
        self.control = ControlPanePresenter(num_batches)
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

    def confirm_load(self, n_clicks, submit):
        """
        Gives a confirm pop up iff any batch has filters.
        If the pop up is not shown we still increment
        the number of submit clicks for the pop-up,
        because we still want to trigger the
        events.
        :param n_clicks: Number of clicks of load
        :param submit: the number of clicks of submit
        :reuturn: if to show the confirm pop=-p and the number
        of submit clicks.
        """
        if self.control._filters.has_filters():
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


    def save_data(self, name, active):
        """
        Saves either a muon histogram nexus file
        for each batch, or a filter file for the
        active batch, from the current muon
        event data.
        :param name: a string of the data type (json
        or nexus) and the name of the file to save to.
        :param active: the index of the active batch
        :returns: the name of the saved file (for nexus, the
        names of the files for each batch, separated by commas)
        :raises GUIError: if the data cannot be saved
        """
        data = self.load.get_data
        if 'None' in name:
            return ''
        dtype = name[0]
        file = name[1:]

        saved = file
        if dtype == 'n':
            # a separate file for each batch, with its index
            saved = ', '.join(batch_file_names(file,
                                               self.control.num_batches))

        print("saving to ", saved)
        try:
            if dtype == "n":
                data.save('all', file, nexus_v3=False)
            elif dtype == 'j':
                data.save_filters(active, file)
        except Exception as error:
            raise GUIError(f'The data could not be '
                           f'saved to {saved}.') from error
        return saved

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
        return self.control._filters._amp.plot(data)

    def load_nxs(self, name, debug_state, active):
        """
        Loads a muon event nexus file.
        :param name: the name of the file to open.
        :param debug_state: if debug mode is on or off.
        :param active: the index of the active batch
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
        The filters and settings are for the active batch.
        :raises GUIError: if the file cannot be read
        """
        if not name or 'None' in name:
            # there is no file, because the file browser was cancelled
            # or because a failed load has put the name back to there
            # being no file (see the except below). The same file check
            # cannot be used, as there is no data to read settings from.
            self.load.set_file(name)
            return (self.plot(), [], True, [], True,
                    *[no_update] * 5,
                    self.control.headers,
                    {},
                    self.control.no_events_str)

        if name == self.load.file:
            # same file, so the data (and the number of
            # events) is unchanged and only the settings
            # are read back
            (times, logs, amp, state,
             min_time, max_time,
             num_bins, headers) = self.control.refresh(active)
            return (self.control._plot.fig,
                    times, False,
                    logs, False,
                    amp, state, min_time, max_time, num_bins,
                    headers,
                    self.control._filters._amp._plot.fig,
                    no_update)
        previous = self.load.file
        self.load.set_file(name)

        try:
            self.load.load_nxs(name, self.control.num_batches)
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
         num_bins, headers) = self.control.refresh(active)

        # any previous number of events was for the old data
        return (self.plot(), times, False,
                logs, False,
                amp, state, min_time, max_time, num_bins,
                headers, self.plot_amps(data),
                self.control.no_events_str)
