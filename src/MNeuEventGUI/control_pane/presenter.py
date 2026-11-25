from dash import no_update
from MNeuEventLib import _get_filter_times

from MNeuEventGUI.control_pane.view import ControlPaneView
from MNeuEventGUI.filters.presenter import FilterPresenter
from MNeuEventGUI.log.presenter import LOG_TABLE
from MNeuEventGUI.plot_area.presenter import PlotAreaPresenter
from MNeuEventGUI.presenter_template import PresenterTemplate
from MNeuEventGUI.time.presenter import TIME_TABLE, TimePresenter
from MNeuEventGUI.utils.batch import (
    INITIAL_BATCHES,
    batch_colour,
    batch_label,
)
from MNeuEventGUI.utils.errors import GUIError


class ControlPanePresenter(PresenterTemplate):
    """
    The control pane contains the
    filters and the plot area.
    This is the presenter for the
    widget. This follows the MVP
    pattern.

    There is one set of filter widgets, which shows the
    active batch (see utils/batch.py).
    """
    def __init__(self, num_batches=INITIAL_BATCHES):
        """
        This creates the presenter object for the
        widget.
        :param num_batches: the number of batches to start with
        """
        self._data = None
        self.num_batches = num_batches
        self._filters = FilterPresenter(num_batches)
        self._plot = PlotAreaPresenter('main')
        self._view = ControlPaneView(self)

    def batch_options(self):
        """
        :returns: the options for the dropdown for
        choosing the batch (one for each batch)
        """
        return [{'label': batch_label(index), 'value': index}
                for index in range(self.num_batches)]

    def batch_controls(self, active, num_batches=None):
        """
        Gets the state of the controls for choosing the batch.
        :param active: the index of the active batch
        :param num_batches: the number of batches (only used
        so this is updated when a batch is added or removed)
        :returns: the dropdown options, if the previous, next and
        remove buttons are disabled and the style of the mark
        showing the active batch's colour
        """
        last = self.num_batches - 1
        return (self.batch_options(),
                active == 0,
                active == last,
                last == 0,
                ControlPaneView.swatch_style(active))

    def previous_batch(self, n_clicks, active):
        """
        Moves to the previous batch.
        :param n_clicks: the number of clicks of the previous button
        :param active: the index of the active batch
        :returns: the index of the new active batch
        """
        return active - 1 if active > 0 else no_update

    def next_batch(self, n_clicks, active):
        """
        Moves to the next batch.
        :param n_clicks: the number of clicks of the next button
        :param active: the index of the active batch
        :returns: the index of the new active batch
        """
        return active + 1 if active < self.num_batches - 1 else no_update

    def add_batch(self, n_clicks=None):
        """
        Adds a batch, after the existing batches,
        and makes it the active one.
        :param n_clicks: the number of clicks of the add button
        :returns: the index of the active batch and
        the number of batches
        """
        if self._data is not None:
            self._data.add_batch()
        self._filters.add_batch()
        self.num_batches += 1
        return self.num_batches - 1, self.num_batches

    def remove_batch(self, n_clicks, active):
        """
        Removes the active batch. The later batches move
        down by one. The next batch (or the previous one,
        if it was the last) becomes active.
        :param n_clicks: the number of clicks of the remove button
        :param active: the index of the batch to remove
        :returns: the index of the active batch and
        the number of batches
        :raises GUIError: if it is the only batch
        """
        if self.num_batches == 1:
            raise GUIError('The only batch cannot be removed.')
        if self._data is not None:
            self._data.remove_batch(active)
        self._filters.remove_batch(active)
        self.num_batches -= 1
        return min(active, self.num_batches - 1), self.num_batches

    def clear(self):
        """
        Clears the stored data when a bad file is
        loaded.
        """
        self._data = None
        self._filters.clear()

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

        name = self._filters._log.get_new_log_name([])
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
            names = [self._filters._log.get_new_log_name([])]
        return names

    def make_plot(self, time_data, log_data, state_changed, active):
        """
        This method creates a plot.
        If no sample logs are selected, it will just plot a
        default. The plot will include shaded regions
        for the data that is kept by each batch, which
        are read from the data (the tables only show the
        active batch).
        :param time_data: the data from the time filter table
        (only used to redraw the plot when it changes)
        :param log_data: the data from the sample log filter table
        (only used to redraw the plot when it changes)
        :param state_changed: the signal for the state of the time
        filters (inc/exc) having changed
        :param active: the index of the active batch
        :returns: an updated figure
        """
        if self._data is None:
            return self.empty()

        log_data = [self._filters._log.load(
                        self._data._dict(batch)['sample_log_filters'])
                    for batch in range(self.num_batches)]
        names = self.plot_log_names(log_data)
        logs = [self._data.dataset.get_sample_log(n) for n in names]
        self._plot.new_plot(names, logs)

        # draw the active batch last, so it is on top
        order = [batch for batch in range(self.num_batches)
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
                y_min, y_max = self._filters.get_log_y_range(row)
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
        self._filters.set_data(data)

    @property
    def headers(self):
        """
        :returns: the column headers
        """
        return self._filters.headers

    @property
    def no_events_str(self):
        """
        :returns: the string for when the number of
        events has not been calculated
        """
        return self._filters.no_events_str

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

    def display_hover(self, hover_info):
        """
        A method for getting the hover text
        for the plot. This will say if data is
        being used in the analysis or not and
        which filters add/remove it, for each batch.
        :param hover_info: the hover data
        :returns: if to show tooltip text, the bounding box for the tooltip
        and the text for the tooltip
        """
        if hover_info is None or self._data is None:
            return False, no_update, no_update
        pt = hover_info['points'][0]
        bbox = pt['bbox']

        lines = []
        for batch in range(self.num_batches):
            filters = self._data._dict(batch)
            rows = self._filters._time.load(filters['time_filters'])
            lines.append(f'{batch_label(batch)}: '
                         + self._keep_text(pt['x'], rows,
                                           filters['time_filter_type']))

        children = self._view.hover_text(pt, lines)
        return True, bbox, children

    def refresh(self, active):
        """
        A method to get the active batch's filters
        and settings from the data.
        :param active: the index of the active batch
        :returns: the values for the filters and settings
        (see FilterPresenter.values)
        """
        return self._filters.values(active)
