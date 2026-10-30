import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, html

from MNeuEventGUI.utils.batch import batch_colour, batch_id, tab_id
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
        # the filter type is picked up from the model, so we trigger
        # off the time table's changed state signal. Using the dropdown
        # directly would race with the callback that updates the model.
        callback(Output('main_plot', 'figure', allow_duplicate=True),
                 [Input(batch_id('time-table', ALL), 'rowData'),
                  Input(batch_id('log-table', ALL), 'rowData'),
                  Input(batch_id('time-table_changed_state', ALL), 'data'),
                  Input('batch-tabs', 'active_tab')],
                 prevent_initial_call=True)(presenter.make_plot)

        callback([Output('main_tooltip', 'show', allow_duplicate=True),
                  Output('main_tooltip', 'bbox', allow_duplicate=True),
                  Output('main_tooltip', 'children', allow_duplicate=True)],
                 Input('main_plot', 'hoverData'),
                 [State(batch_id('time-table', ALL), 'rowData'),
                  State(batch_id('time-table_dropdown', ALL), 'value')],
                 prevent_initial_call=True)(presenter.display_hover)

        # calculating updates the number of events for every batch
        callback(Output(batch_id('N_events', ALL), 'children',
                        allow_duplicate=True),
                 Input(batch_id('calc_btn', ALL), 'n_clicks'),
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
