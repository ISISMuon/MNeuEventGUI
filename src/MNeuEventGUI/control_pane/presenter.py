from MuonDataLib.GUI.presenter_template import PresenterTemplate
from MuonDataLib.GUI.filters.presenter import FilterPresenter
from MuonDataLib.GUI.plot_area.presenter import PlotAreaPresenter
from MuonDataLib.GUI.control_pane.view import ControlPaneView
from MuonDataLib.filters import Filters

from dash import no_update
import numpy as np


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
        self._plot = PlotAreaPresenter('main')
        self._filter = FilterPresenter()
        self._view = ControlPaneView(self)

    def clear(self):
        """
        Clears the stored data when a bad file is
        loaded.
        """
        self._filter._data = None
        self._filter._log._logs = None

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
        if self._filter._data is None:
            return self.empty()

        name = self._filter._log.get_new_log_name([])
        return self._plot.new_plot([name], self._filter._log._logs)

    def make_plot(self, time_data, log_data, amp_data, state):
        """
        This method creates a plot.
        If no sample logs are selected, it will just plot a
        default. The plot will include shaded regions
        for the data that is kept.
        :param time_data: the data from the time filter table
        :param log_data: the data from the sample log filter table.
        :param amp_data: the amplitudes from the sample log filter table.
        Its also used to get which plots to make.
        :param state: the state of the time filters (inc/exc)
        :returns: an updated figure
        """
        if self._filter._data is None:
            return self.empty()

        names = [row['sample_log-table'] for row in log_data]
        if len(names) == 0:
            names = [self._filter._log.get_new_log_name([])]
        self._plot.new_plot(names, self._filter._log._logs)
        start, stop, msg = self._filter.update_filters(time_data,
                                                       state,
                                                       log_data,
                                                       amp_data)

        self.add_filters(start, stop, log_data)

        return self._plot.fig

    def _loop_over_filters(self, func, f_start, f_stop, *kwargs):
        """
        This loops over the exclude filter start and end times
        and creates the plot. Including shaded regions for
        the data that is kept.
        :param func: The plotting function to be used
        :param f_start: the start times for the exclude filter
        :param f_end: the end times for the exclude filter
        :param kwargs: additional arguments for func
        """
        func(self._plot._min, f_start[0], *kwargs)
        for k in range(1, len(f_start)):
            func(f_stop[k-1], f_start[k], *kwargs)

        func(f_stop[-1], self._plot._max, *kwargs)

    def wrap_add_shaded_region(self, x0, xN, *kargs):
        """
        A wrapper for adding a shaded region (only
        time filters).
        :param x0: the start x value
        :param xN: the end x value
        :param kwargs: extra arguments, not used
        """
        self._plot.add_shaded_region(x0, xN)

    def wrap_add_rect(self, x0, xN, y0, yN, ax):
        """
        A wrapper for adding a shaded recrangle (if
        using at least one log filter).
        :param x0: the start x value
        :param xN: the end x value
        :param y0: the start y value
        :param yN: the end y value
        :param ax: the axis to add the rectangle to
        """
        self._plot.add_rect(x0, y0, xN, yN, ax)

    def add_filters(self, start, stop, log_data):
        """
        This gets the filters for that data,
        as defined by the tables, and plots
        shaded regions corresponding to the
        kept data.
        :param start: the start times for the filters
        (both time and log)
        :param end: the end times for the filters
        (both time and log)
        :param log_data: the log values from
        the sample log table.
        """
        if len(start) == 0:
            # no filters
            self.wrap_add_shaded_region(self._plot._min,
                                        self._plot._max)
            return

        N = len(log_data) if len(log_data) > 0 else 1
        axis = [str(k + 1) for k in range(N)]

        #  first axis has no number, second is number 2
        axis[0] = ''

        if len(start) == 0:
            # no filters
            new_start = [self._plot._min]
            new_stop = [self._plot._max]
        else:
            new_start, new_stop = self._filter.filters_rm_overlaps(start, stop)
        if len(log_data) == 0:
            # If only have time filters
            self._loop_over_filters(self.wrap_add_shaded_region,
                                    new_start,
                                    new_stop)
            return

        # loop over plots (sample logs)
        for k, ax in enumerate(axis):
            y_min, y_max = self._filter.get_log_y_range(log_data[k])
            self._plot.add_hline(y_min)
            self._plot.add_hline(y_max)
            self._loop_over_filters(self.wrap_add_rect,
                                    new_start,
                                    new_stop,
                                    y_min,
                                    y_max,
                                    ax)

    def add_time_filters(self, time_data, state):
        """
        This methods adds filters to the plot.
        A filter is represented by removing the shaded
        region from the plot. i.e. only the shaded
        data is used in calculations.
        :param data: the data from the filter table
        :param state: if the filter is an exclude or include
        :returns: an updated figure
        """
        self._plot.fig.layout.shapes = []
        if len(time_data) == 0 and state == 'Exclude':
            self._plot.add_shaded_region(self._plot._min, self._plot._max)
            return self._plot.fig

        start = []
        end = []
        # add the filters back
        if state == 'Include':
            for filter_details in time_data:
                span = self._filter._time.get_range(filter_details)
                self._plot.add_shaded_region(*span)
        else:
            for filter_details in time_data:
                tmp = self._filter._time.get_range(filter_details)
                start.append(tmp[0])
                end.append(tmp[1])
            self.apply_exc_data(start, end)
        return self._plot.fig

    def apply_exc_data(self, start, end):
        """
        Applys the exclusion of data from
        the analysis. i.e. the area is not
        shaded.
        :param start: A list of start values
        for the exluded regions
        :param end: A list of end values
        for the excluded regions
        """
        if len(start) == 0:
            return

        sorted_start = np.sort(start)
        sorted_end = np.sort(end)

        f_start = [sorted_start[0]]
        f_end = []

        for j in range(len(sorted_start)-1):
            if sorted_start[j+1] > sorted_end[j]:
                f_end.append(sorted_end[j])
                f_start.append(sorted_start[j+1])
        f_end.append(sorted_end[-1])

        self._plot.add_shaded_region(self._plot._min, f_start[0])
        for j in range(1, len(f_start)):
            self._plot.add_shaded_region(f_end[j-1], f_start[j])

        self._plot.add_shaded_region(f_end[-1], self._plot._max)

    def set_data(self, data):
        """
        A simple setter for the MuonEventData
        Will also reset the range for the plot
        :param data: MuonEventData
        """
        self._plot.reset_plot_range()
        self._filter.set_data(data)

    @property
    def headers(self):
        """
        :returns: the column headers
        """
        return self._filter.headers

    def display_hover(self, hover_info, filters, state):
        """
        A method for getting the hover text
        for the plot. This will say if data is
        being used in the analysis or not and
        which filters add/remove it.
        :param hover_info: the hover data
        :param filters: the time filters
        :param state: if the filter is an exclude or include
        :returns: if to show tooltip text, the bounding box for the tooltip
        and the text for the tooltip
        """
        if hover_info is None:
            return False, no_update, no_update
        pt = hover_info['points'][0]
        bbox = pt['bbox']
        added = []
        removed = []
        txt = 'Keep data: '

        if state == 'Include':
            for filter_details in filters:
                start, end = self._filter._time.get_range(filter_details)
                if start <= pt['x'] and end >= pt['x']:
                    added.append(filter_details['Name_time-table'])
            if len(added) > 0:
                txt += 'True. '
                txt += 'Added by: '
                for name in added:
                    txt += name + ', '
            else:
                txt += 'False'

        else:
            for filter_details in filters:
                start, end = self._filter._time.get_range(filter_details)
                if (start <= pt['x'] and end >= pt['x']):
                    removed.append(filter_details['Name_time-table'])
            if len(removed) > 0:
                txt += 'False. '
                txt += 'Removed by: '
                for name in removed:
                    txt += name + ', '
            else:
                txt += 'True'

        children = self._view.hover_text(pt, txt)
        return True, bbox, children

    def read_filter(self, name):
        """
        A method to get the filters from a file
        and populate the GUI.
        :param name: the name of the json file
        :returns: the filter data, the state for the time filter
        (include/exclude) and the column headers
        """
        data = Filters.from_json(name)
        return self._filter.load(data)
