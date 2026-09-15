from dash import html, callback, Output, Input
import dash_bootstrap_components as dbc

from MuonDataLib.GUI.view_template import ViewTemplate


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
                dbc.Col(dbc.Input(id='min-time',
                                  value=0.,
                                  type='number',
                                  debounce=True,
                                  placeholder=0.)),
                dbc.Col(dbc.Input(id='max-time',
                                  value=32.768,
                                  type='number',
                                  debounce=True,
                                  placeholder=32.768)),
                ]),
            dbc.Row(
                dbc.Col(["Number of bins:",
                     dbc.Input(id='num-bin',
                               value=2048,
                               type='number',
                               step=1,
                               placeholder=2048),
                ])),
            dbc.Row([html.Div(id="display-width"),
                ]),
            ])

    def set_callbacks(self, presenter):
        """
        Set callbacks required by the GUI.
        """
        # callback to update resolution display
        callback(Output('display-width', 'children'),
                 Input('min-time', 'value'),
                 Input('max-time', 'value'),
                 Input('num-bin', 'value'))(presenter.display_width)

        # callback to mark number of bins if invalid
        callback(Output('num-bin', 'invalid'),
                 Input('num-bin', 'value'))(presenter.check_num_bins_invalid)

        # callback to mark min or max time if invalid
        callback([Output('min-time', 'invalid'),
                  Output('max-time', 'invalid')],
                 [Input('min-time', 'value'),
                  Input('max-time', 'value')])(presenter.check_range_invalid)
