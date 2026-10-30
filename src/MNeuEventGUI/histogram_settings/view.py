import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

from MNeuEventGUI.view_template import ViewTemplate


class HistSettingsView(ViewTemplate):
    """
    A class for the view of the histogram settings widget.
    """

    def generate(self, presenter):
        """
        Generate the histogram settings widget.
        :param presenter: The presenter for the widget.
        :returns: The layout for the GUI widget.
        """
        return html.Div([
            "Minimum and maximum time:",
            dbc.Row([
                dbc.Col(dbc.Input(id=presenter.component_id('min-time'),
                                  value=0.,
                                  type='number',
                                  debounce=True,
                                  placeholder=0.)),
                dbc.Col(dbc.Input(id=presenter.component_id('max-time'),
                                  value=32.768,
                                  type='number',
                                  debounce=True,
                                  placeholder=32.768)),
                ]),
            dbc.Row(
                dbc.Col(["Number of bins:",
                     dbc.Input(id=presenter.component_id('num-bins'),
                               value=2048,
                               type='number',
                               step=1,
                               placeholder=2048),
                ])),
            dbc.Row([html.Div(id=presenter.component_id('display-width')),
                ]),
            ])

    def set_callbacks(self, presenter):
        """
        Set callbacks required by the GUI.
        """
        min_time = presenter.component_id('min-time')
        max_time = presenter.component_id('max-time')
        num_bins = presenter.component_id('num-bins')
        display_width = presenter.component_id('display-width')

        # callback to update resolution display
        callback(Output(display_width, 'children'),
                 Input(min_time, 'value'),
                 Input(max_time, 'value'),
                 Input(num_bins, 'value'))(presenter.display_width)

        # callback to update data when values change
        callback(Input(min_time, 'value'),
                 Input(max_time, 'value'),
                 Input(num_bins, 'value'),
                 prevent_initial_call=True)(presenter.set_values)

        # callback to mark number of bins if invalid
        callback(Output(num_bins, 'invalid'),
                 Input(num_bins, 'value'))(presenter.check_num_bins_invalid)

        # callback to mark min or max time if invalid
        callback([Output(min_time, 'invalid'),
                  Output(max_time, 'invalid')],
                 [Input(min_time, 'value'),
                  Input(max_time, 'value')])(presenter.check_range_invalid)
