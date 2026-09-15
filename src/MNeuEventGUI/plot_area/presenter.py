from MuonDataLib.GUI.presenter_template import PresenterTemplate
from MuonDataLib.GUI.plot_area.view import PlotAreaView
import plotly
from plotly.subplots import make_subplots
import numpy as np


class PlotAreaPresenter(PresenterTemplate):
    """
    A class for the plotting widget's presenter.
    This follows the MVP pattern.
    """

    def __init__(self, ID):
        """
        Creates a Plot Area Presenter.
        This widget deals with plotly.
        We have multiple plots, so need a
        way to tell them apart.
        :param ID: the ID (unique name) for
        the plot presenter.
        """
        self.ID = ID
        self._view = PlotAreaView(self)
        self.reset_plot_range()
        self.fig = None

    def reset_plot_range(self):
        """
        Resets the plot range.
        So when new data is plotted
        it will correctly get the
        min and max time values.
        """
        self._min = 1000
        self._max = -1000

    def add_hline(self, value):
        """
        Adds a horizontal line at
        value.
        :param value: the y value to
        place the line at
        """
        self.fig.add_hline(y=value,
                           line_width=2,
                           line_dash='dash',
                           line_color='gray')

    def add_vline(self, value):
        """
        Adds a vertical line at
        value.
        :param value: the y value to
        place the line at
        """
        self.fig.add_vline(x=value,
                           line_width=2,
                           line_dash='dash',
                           line_color='gray')

    def add_rect(self, x0, y0, x1, y1, axis):
        """
        Adds a rectangle to a specific subplot.
        :param x0: the x value for the bottom left corner
        :param y0: the y value for the bottom left corner
        :param x1: the x value for the top right corner
        :param y1: the y value for the top right corner
        :param axis: the subplot to add the rectanlge to
        """
        self.fig.add_shape(type='rect',
                           xref=f'x{axis}',
                           yref=f'y{axis}',
                           x0=x0,
                           y0=y0,
                           x1=x1,
                           y1=y1,
                           fillcolor='PaleGreen',
                           opacity=0.3,
                           layer='above',
                           line={'color': 'black',
                                 'width': 4})

    def add_shaded_region(self, start, stop):
        """
        Adds a shaded region to the plot.
        :param start: when to start the shaded
        region
        :param stop: when to stop the shaded region
        """
        self.fig.add_vrect(x0=start,
                           x1=stop,
                           opacity=0.3,
                           fillcolor='PaleGreen',
                           layer='above',
                           line={'color': 'black',
                                 'width': 4})

    def shade_all(self):
        """
        For a new main plot, lets assume all of
        the data is shaded (included)
        """
        self.add_shaded_region(self._min, self._max)

    def new_plot(self, names, logs):
        """
        A method to create a plot from the
        sample logs. This will always create a
        fresh plot.
        :param names: a list of sample log names
        to plot
        :param logs: the sample logs object
        :returns the figure object
        """
        x_list = []
        y_list = []
        for name in names:
            log_data = logs.get_sample_log(name)
            x, y = log_data.get_original_values()
            x_list.append(x)
            y_list.append(y)
        return self.plot(names, x_list, y_list)

    def add_trace(self, x, y, name, row, col):
        """
        A simple wrapper for the plotly scatter
        method. This is done to make mocking easier
        :param x: the x data
        :param y: the y data
        :param name: the label for the data
        :param row: the subplot row to place the data into
        :param col: the subplot col to place the data into
        """
        self.fig.add_trace(plotly.graph_objects.Scatter(
                    x=x,
                    y=y,
                    name=name,
                    mode='lines'
                    ),
                          row, col)

    def plot(self, labels, x_list, y_list, x_title='time'):
        """
        A method to plot a list of data as a vertically
        stacked figure. All of the list must match
        i.e. be in the same order.
        :param labels: the list of labels for the data
        :param x_list: a list of x values (list of lists)
        :param y_list: a list of y values (list of lists)
        :returns: the figure object
        """
        N = len(labels)

        if N == 0:
            return self.fig

        # only stack vertically
        self.fig = make_subplots(rows=N,
                                 cols=1,
                                 x_title=x_title,
                                 shared_xaxes=True,
                                 vertical_spacing=0.02,
                                 start_cell='top-left')
        self._height = 900
        self.fig.update_layout(height=self._height)

        # add data to the subplots
        for i, name in enumerate(labels):
            x = x_list[i]
            # plot lines as this is much faster than points
            self.add_trace(x,
                           y_list[i],
                           name,
                           i + 1,
                           1)
            if self._min > np.min(x):
                self._min = np.min(x)

            if self._max < np.max(x):
                self._max = np.max(x)
            self.fig.update_traces(hoverinfo='none')
            self.fig.update_yaxes(title_text=name, row=i+1, col=1)
            # manually set y limits for subplots
            y_min = np.min(y_list[i])
            y_max = np.max(y_list[i])
            # padding for the plot of 3% of the data range
            dy = (y_max - y_min)*0.03
            self.fig.update_yaxes(range=[y_min - dy,
                                         y_max + dy],
                                  row=i+1)
        return self.fig
