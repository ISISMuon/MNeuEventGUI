import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html

from MNeuEventGUI.utils.batch import batch_id
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
        batch = presenter.batch
        return html.Div([
            "Minimum and maximum time:",
            dbc.Row([
                dbc.Col(dbc.Input(id=batch_id('min-time', batch),
                                  value=0.,
                                  type='number',
                                  debounce=True,
                                  placeholder=0.)),
                dbc.Col(dbc.Input(id=batch_id('max-time', batch),
                                  value=32.768,
                                  type='number',
                                  debounce=True,
                                  placeholder=32.768)),
                ]),
            dbc.Row(
                dbc.Col(["Number of bins:",
                     dbc.Input(id=batch_id('num-bins', batch),
                               value=2048,
                               type='number',
                               step=1,
                               placeholder=2048),
                ])),
            dbc.Row([html.Div(id=batch_id('display-width', batch)),
                ]),
            ])

    def set_callbacks(self, presenter):
        """
        Set callbacks required by the GUI.
        """
        min_time = batch_id('min-time', presenter.batch)
        max_time = batch_id('max-time', presenter.batch)
        num_bins = batch_id('num-bins', presenter.batch)
        display_width = batch_id('display-width', presenter.batch)

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
