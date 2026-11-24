
from itertools import count

from dash import Patch, no_update
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
from MNeuEventGUI.utils.batch_callback import (
    clear_registry,
    unregister_batch,
)
from MNeuEventGUI.utils.errors import GUIError


class ControlPanePresenter(PresenterTemplate):
    """
    The control pane contains the
    filters and the plot area.
    This is the presenter for the
    widget. This follows the MVP
    pattern.
    """
    def __init__(self, num_batches=INITIAL_BATCHES):
        """
        This creates the presenter object for the
        widget.
        :param num_batches: the number of batches to start with
        """
        self._data = None
        # the keys restart from 0, so forget the
        # batches of any previous control pane
        clear_registry()

        # the keys for the IDs of each batch's components
        self._keys = count()
        # the last number of clicks of each button for
        # choosing, adding and removing batches
        self._clicks = {}

        # one set of filters per batch, in the order of
        # the batches in the data
        self._filters = [FilterPresenter(next(self._keys))
                         for _ in range(num_batches)]
        self._plot = PlotAreaPresenter('main')
        self._view = ControlPaneView(self)

    @property
    def num_batches(self):
        """
        :returns: the number of batches
        """
        return len(self._filters)

    @property
    def batch_keys(self):
        """
        :returns: the key of each batch, in batch order
        """
        return [filter_presenter.key for filter_presenter in self._filters]

    def order(self):
        """
        Gets the order of the batches for the callbacks
        that use every batch (see ordered_callback).
        :returns: the key of each batch, in batch order
        """
        return self.batch_keys

    def index_of(self, key):
        """
        Gets the index of a batch from its key.
        :param key: the key of the batch (e.g. the active tab)
        :returns: the index of the batch, the first batch
        if it is not a current batch
        """
        keys = self.batch_keys
        return keys.index(key) if key in keys else 0

    def active_index(self, key):
        """
        Gets the index of the active batch, for actions
        that change or save a single batch's data (so it
        must not quietly fall back to another batch).
        :param key: the key of the active batch
        :returns: the index of the batch
        :raises GUIError: if it is not a current batch
        """
        keys = self.batch_keys
        if key not in keys:
            raise GUIError('The selected batch no longer exists. '
                           'Please choose a batch and try again.')
        return keys.index(key)

    def _new_click(self, name, n_clicks):
        """
        Checks if a button has been clicked since it was
        last checked, as Dash can re-trigger a callback
        without a new click when the page changes.
        :param name: the name of the button
        :param n_clicks: the button's number of clicks
        (None means it is not from a button)
        :returns: if it is a new click
        """
        if n_clicks is None:
            return True
        if n_clicks <= self._clicks.get(name, 0):
            return False
        self._clicks[name] = n_clicks
        return True

    def batch_options(self):
        """
        :returns: the options for the dropdown for
        choosing the batch (one for each batch)
        """
        return [{'label': batch_label(index), 'value': key}
                for index, key in enumerate(self.batch_keys)]

    def batch_controls(self, active, keys):
        """
        Gets the state of the controls for choosing the batch.
        :param active: the key of the active batch
        :param keys: the key of each batch (so this is updated
        when a batch is added or removed)
        :returns: the dropdown options, if the previous, next and
        remove buttons are disabled and the style of the mark
        showing the active batch's colour
        """
        index = self.index_of(active)
        last = self.num_batches - 1
        return (self.batch_options(),
                index == 0,
                index == last,
                last == 0,
                ControlPaneView.swatch_style(index))

    def _step(self, active, step, name, n_clicks):
        """
        Moves to a neighbouring batch.
        :param active: the key of the active batch
        :param step: how many batches to move by
        :param name: the name of the button
        :param n_clicks: the button's number of clicks
        :returns: the key of the new active batch
        """
        index = self.index_of(active) + step
        if (not self._new_click(name, n_clicks)
                or not 0 <= index < self.num_batches):
            return no_update
        return self.batch_keys[index]

    def previous_batch(self, n_clicks, active):
        """
        Moves to the previous batch.
        :param n_clicks: the number of clicks of the previous button
        :param active: the key of the active batch
        :returns: the key of the new active batch
        """
        return self._step(active, -1, 'previous', n_clicks)

    def next_batch(self, n_clicks, active):
        """
        Moves to the next batch.
        :param n_clicks: the number of clicks of the next button
        :param active: the key of the active batch
        :returns: the key of the new active batch
        """
        return self._step(active, 1, 'next', n_clicks)

    def show_batch(self, active):
        """
        Shows the active batch's filters and hides the others.
        :param active: the key of the active batch
        :returns: the style of each batch's filters (in batch order)
        """
        index = self.index_of(active)
        return [self._view.pane_style(k == index)
                for k in range(self.num_batches)]

    def add_batch(self, n_clicks=None):
        """
        Adds a batch, after the existing batches,
        and makes it the active one.
        :param n_clicks: the number of clicks of the add button
        (None to always add)
        :returns: the change to the batches' filters,
        the key of the active batch and the key of each batch
        """
        if not self._new_click('add', n_clicks):
            return (no_update,) * 3

        index = self.num_batches
        filter_presenter = FilterPresenter(next(self._keys))
        filter_presenter.set_index(index)
        if self._data is not None:
            self._data.add_batch()
            filter_presenter.set_data(self._data)
        self._filters.append(filter_presenter)

        # hide the other batches in the same change that shows the
        # new one, otherwise both are shown until show_batch runs
        panes = Patch()
        for other in range(index):
            panes[other]['props']['style'] = self._view.pane_style(False)
        panes.append(self._view.pane(filter_presenter, True))
        return panes, filter_presenter.key, self.batch_keys

    def remove_batch(self, n_clicks, active):
        """
        Removes the active batch. The later batches move
        down by one in the data, but their components keep
        their IDs. The next batch (or the previous one, if
        it was the last) becomes active.
        :param n_clicks: the number of clicks of the remove button
        (None to always remove)
        :param active: the key of the batch to remove
        :returns: the change to the batches' filters,
        the key of the active batch and the key of each batch
        :raises GUIError: if it is the only batch
        """
        keys = self.batch_keys
        if active not in keys or not self._new_click('remove', n_clicks):
            return (no_update,) * 3
        if len(keys) == 1:
            raise GUIError('The only batch cannot be removed.')

        index = keys.index(active)
        if self._data is not None:
            self._data.remove_batch(index)
        del self._filters[index]
        unregister_batch(active)
        for later in range(index, self.num_batches):
            self._filters[later].set_index(later)

        # show the new active batch in the same change that removes
        # the old one, otherwise none are shown until show_batch runs
        new_index = min(index, self.num_batches - 1)
        panes = Patch()
        del panes[index]
        panes[new_index]['props']['style'] = self._view.pane_style(True)
        return panes, self.batch_keys[new_index], self.batch_keys

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

    def make_plot(self, time_data, log_data, state_changed, active,
                  keys=None):
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
        :param active: the key of the active batch
        :param keys: the key of each batch (so the plot is
        redrawn when a batch is added or removed)
        :returns: an updated figure
        """
        if self._data is None:
            return self.empty()

        names = self.plot_log_names(log_data)
        logs = [self._data.dataset.get_sample_log(n) for n in names]
        self._plot.new_plot(names, logs)

        # draw the active batch last, so it is on top
        active = self.index_of(active)
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
        Dash also runs this when a batch is added or removed
        (as the ALL input changes), so it only calculates if
        a calculate button has a new click.
        :param n_clicks: the number of button
        presses for each calculate button, in batch order
        :returns: The number of events to display
        for each batch
        :raises GUIError: if no data is loaded
        :raises RuntimeError: if the filters cannot be applied
        """
        # check every button, so all of the counts are kept up to date
        new_clicks = [self._new_click(f'calc_{key}', clicks)
                      for key, clicks in zip(self.batch_keys, n_clicks)
                      if clicks is not None]
        if not any(new_clicks):
            return no_update
        if self._data is None:
            raise GUIError('Please load a file before calculating.')
        self._data.calculate()
        return [filter_presenter.n_events
                for filter_presenter in self._filters]

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
