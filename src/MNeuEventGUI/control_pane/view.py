import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html

from MNeuEventGUI.log.presenter import LOG_TABLE
from MNeuEventGUI.plot_area.view import PLOT, TOOLTIP
from MNeuEventGUI.table.view import CHANGED_STATE
from MNeuEventGUI.time.presenter import TIME_TABLE
from MNeuEventGUI.time.view import DROPDOWN
from MNeuEventGUI.utils.batch import all_batches, batch_colour, tab_id
from MNeuEventGUI.view_template import ViewTemplate


class ControlPaneView(ViewTemplate):
    """
    Creates the main dash app for event filtering.
    """

    def generate(self, presenter):
        """
        Create the view for the app
        :param presenter: the presenter for the widget
        :returns: the app's view
        """

        # set width of the filter tables
        filter_width = 2

        # a tab of filters for each batch
        tabs = dbc.Tabs([
            dbc.Tab(filter_presenter.layout,
                    label=f'Batch {filter_presenter.batch}',
                    tab_id=tab_id(filter_presenter.batch),
                    label_style={'color':
                                 batch_colour(filter_presenter.batch),
                                 'fontWeight': 'bold'})
            for filter_presenter in presenter._filters],
                        id='batch-tabs',
                        active_tab=tab_id(0))

        # setup the layout
        return dbc.Row([
                    dbc.Col(tabs, width=filter_width),
                    dbc.Col(presenter._plot.layout, width=12-filter_width)
                    ],
                        className="g-0", align='center')

    def set_callbacks(self, presenter):
        """
        Set the callbacks for the widget
        :param pressenter: the presenter for the widget
        """
        plot = presenter._plot.component_id(PLOT)
        tooltip = presenter._plot.component_id(TOOLTIP)

        # the filter type is picked up from the model, so we trigger
        # off the time table's changed state signal. Using the dropdown
        # directly would race with the callback that updates the model.
        callback(Output(plot, 'figure', allow_duplicate=True),
                 [Input(all_batches(TIME_TABLE), 'rowData'),
                  Input(all_batches(LOG_TABLE), 'rowData'),
                  Input(all_batches(TIME_TABLE + CHANGED_STATE), 'data'),
                  Input('batch-tabs', 'active_tab')],
                 prevent_initial_call=True)(presenter.make_plot)

        callback([Output(tooltip, 'show', allow_duplicate=True),
                  Output(tooltip, 'bbox', allow_duplicate=True),
                  Output(tooltip, 'children', allow_duplicate=True)],
                 Input(plot, 'hoverData'),
                 [State(all_batches(TIME_TABLE), 'rowData'),
                  State(all_batches(TIME_TABLE + DROPDOWN), 'value')],
                 prevent_initial_call=True)(presenter.display_hover)

        # calculating updates the number of events for every batch
        callback([Output(all_batches('N_events'), 'children',
                         allow_duplicate=True),
                  Output('error_msg', 'children', allow_duplicate=True)],
                 Input(all_batches('calc_btn'), 'n_clicks'),
                 prevent_initial_call=True)(presenter.calculate)

    def hover_text(self, pt, lines):
        """
        A method to generate the text for the tooltip
        (hover text).
        :param pt: the information about the point being hovered on
        :param lines: the status text for each batch
        :returns: An updated layout for the tooltip
        """
        children = html.Div([
            html.H5('Data Point'),
            html.P(f"x: {pt['x']:.3f},  y: {pt['y']:.3f}"),
            html.H5('Status'),
            *[html.P(line) for line in lines]
            ])
        return children
