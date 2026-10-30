
from dash import no_update
from MNeuEventLib import _get_filter_times

from MNeuEventGUI.control_pane.view import ControlPaneView
from MNeuEventGUI.filters.presenter import FilterPresenter
from MNeuEventGUI.log.presenter import LOG_TABLE
from MNeuEventGUI.plot_area.presenter import PlotAreaPresenter
from MNeuEventGUI.presenter_template import PresenterTemplate
from MNeuEventGUI.time.presenter import TIME_TABLE, TimePresenter
from MNeuEventGUI.utils.batch import NUM_BATCHES, active_batch, batch_colour


class ControlPanePresenter(PresenterTemplate):
    """
    The control pane contains the
    filters and the plot area.
    This is the presenter for the
    widget. This follows the MVP
    pattern.
    """
    def __init__(self):
        """
        This creates the presenter object for the
        widget.
        """
        self._data = None

        # one set of filters per batch
        self._filters = [FilterPresenter(batch)
                         for batch in range(NUM_BATCHES)]
        self._plot = PlotAreaPresenter('main')
        self._view = ControlPaneView(self)

    def clear(self):
        """
        Clears the stored data when a bad file is
        loaded.
        """
        self._data = None
        for filter_presenter in self._filters:
            filter_presenter.clear()

    def empty(self):
        """
        A method to return an empty plot, for loading
        bad file after a good one.
        :returns: an empty plot
        """
        return self._plot.plot([''], [[1]], [[1]])

    def plot_default(self):
        """
        This method generates the default plot (for
        after initial load). It will automatically
        get the default sample log.
        :returns: the figure object
        """
        if self._data is None:
            return self.empty()

        name = self._filters[0]._log.get_new_log_name([])
        log = self._data.dataset.get_sample_log(name)
        return self._plot.new_plot([name], [log])

    def plot_log_names(self, log_data):
        """
        Gets the names of the sample logs to plot.
        This is every sample log that is filtered on
        by at least one batch, in order of first
        appearance. If there are none, it is the
        default sample log.
        :param log_data: the sample log table data
        for each batch
        :returns: the names of the sample logs
        """
        names = []
        for table in log_data:
            for row in table:
                name = row['sample_' + LOG_TABLE]
                if name not in names:
                    names.append(name)
        if len(names) == 0:
            names = [self._filters[0]._log.get_new_log_name([])]
        return names

    def make_plot(self, time_data, log_data, state_changed, active_tab):
        """
        This method creates a plot.
        If no sample logs are selected, it will just plot a
        default. The plot will include shaded regions
        for the data that is kept by each batch.
        :param time_data: the data from the time filter table,
        for each batch
        :param log_data: the data from the sample log filter table,
        for each batch. Its also used to get which plots to make.
        :param state_changed: the signal for the state of the time
        filters (inc/exc) having changed, for each batch
        :param active_tab: the ID of the active batch tab
        :returns: an updated figure
        """
        if self._data is None:
            return self.empty()

        names = self.plot_log_names(log_data)
        logs = [self._data.dataset.get_sample_log(n) for n in names]
        self._plot.new_plot(names, logs)

        # draw the active batch last, so it is on top
        active = active_batch(active_tab)
        order = [batch for batch in range(len(self._filters))
                 if batch != active] + [active]

        for batch in order:
            start, stop = _get_filter_times(batch, self._data)

            filters = self._data._dict(batch)
            if start or not (filters["time_filters"]
                             or filters["sample_log_filters"]):
                start = [x * 1e-9 for x in start]
                stop = [x * 1e-9 for x in stop]
                self.add_filter_shading(batch, start, stop,
                                        log_data[batch], names,
                                        batch == active)

        return self._plot.fig

    def add_filter_shading(self, batch, start, stop,
                           log_data, names, outline):
        """
        This plots shaded regions corresponding
        to the data kept by a batch, as defined by
        its tables.
        :param batch: the index of the batch
        :param start: the start times for the filters
        (both time and log)
        :param stop: the end times for the filters
        (both time and log)
        :param log_data: the log values from
        the batch's sample log table.
        :param names: the names of the plotted sample logs
        :param outline: if to outline the shaded regions
        """
        colour = batch_colour(batch)
        # with no filters, all of the data is kept
        intervals = (list(zip(start, stop))
                     or [(self._plot._min, self._plot._max)])

        if len(log_data) == 0:
            # If only have time filters
            for x0, x1 in intervals:
                self._plot.add_shaded_region(x0, x1, colour, outline)
            return

        # loop over plots (sample logs)
        for k, name in enumerate(names):
            #  first axis has no number, second is number 2
            ax = str(k + 1) if k > 0 else ''
            rows = [row for row in log_data
                    if row['sample_' + LOG_TABLE] == name]

            if len(rows) == 0:
                # the batch does not filter on this sample log
                for x0, x1 in intervals:
                    self._plot.add_rect(x0, 0, x1, 1, ax,
                                        colour, outline, domain=True)

            for row in rows:
                y_min, y_max = self._filters[batch].get_log_y_range(row)
                self._plot.add_hline(y_min, row=k + 1, colour=colour)
                self._plot.add_hline(y_max, row=k + 1, colour=colour)
                for x0, x1 in intervals:
                    self._plot.add_rect(x0, y_min, x1, y_max, ax,
                                        colour, outline)

    def set_data(self, data):
        """
        A simple setter for the Data
        Will also reset the range for the plot
        :param data: MuonEventData
        """
        self._plot.reset_plot_range()
        self._data = data
        for filter_presenter in self._filters:
            filter_presenter.set_data(data)

    @property
    def headers(self):
        """
        :returns: the column headers for each batch
        """
        return [filter_presenter.headers
                for filter_presenter in self._filters]

    @property
    def no_events_str(self):
        """
        :returns: the string for when the number of
        events has not been calculated
        """
        return self._filters[0].no_events_str

    def calculate(self, n_clicks):
        """
        A method to calculate the number of
        events that would be used to make
        the histogram for each batch.
        :param n_clicks: the number of button
        presses for each calculate button
        :returns: The number of events to display
        for each batch, the error message (if there is one)
        """
        try:
            _ = self._data.calculate()
        except RuntimeError as msg:
            return ([filter_presenter._view.get_N(0)
                     for filter_presenter in self._filters],
                    str(msg))
        return ([filter_presenter.n_events
                 for filter_presenter in self._filters],
                '')

    @staticmethod
    def _keep_text(x, filters, state):
        """
        Gets the text for if a batch keeps the data
        at a point, and which filters add/remove it.
        :param x: the x value of the point
        :param filters: the batch's time filters
        :param state: if the filter is an exclude or include
        :returns: the text
        """
        names = []
        for filter_details in filters:
            start, end = TimePresenter.get_range(filter_details)
            if start <= x and end >= x:
                names.append(filter_details['Name_' + TIME_TABLE])

        include = state == 'Include'
        # included data is kept iff a filter covers it
        txt = f'Keep data: {bool(names) == include}'
        if names:
            txt += f". {'Added' if include else 'Removed'} by: "
            txt += ', '.join(names)
        return txt

    def display_hover(self, hover_info, filters, states):
        """
        A method for getting the hover text
        for the plot. This will say if data is
        being used in the analysis or not and
        which filters add/remove it, for each batch.
        :param hover_info: the hover data
        :param filters: the time filters for each batch
        :param states: if the filter is an exclude or include,
        for each batch
        :returns: if to show tooltip text, the bounding box for the tooltip
        and the text for the tooltip
        """
        if hover_info is None:
            return False, no_update, no_update
        pt = hover_info['points'][0]
        bbox = pt['bbox']

        lines = [f'Batch {batch}: '
                 + self._keep_text(pt['x'], batch_filters, state)
                 for batch, (batch_filters, state)
                 in enumerate(zip(filters, states))]

        children = self._view.hover_text(pt, lines)
        return True, bbox, children

    def refresh(self):
        """
        A method to get the filters and settings
        from the data.
        :returns: the values for the filters and settings
        (see FilterPresenter.read_values), each as a list
        with a value for each batch
        """
        return [list(values) for values in
                zip(*[filter_presenter.refresh()
                      for filter_presenter in self._filters])]
