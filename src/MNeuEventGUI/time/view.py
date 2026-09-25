from dash import dcc, html, callback, Input

from MNeuEventGUI.table.view import TableView


class TimeView(TableView):
    """
    A class for the view of the filter
    widget. This follows the MVP
    pattern.
    """
    def generate(self, presenter):
        """
        Creates the filter widget's GUI.
        :returns: the layout of the widget's
        GUI.
        """

        return html.Div([
            html.Div([html.P('Filter Type:'),
                     dcc.Dropdown(['Include', 'Exclude'],
                                  'Include',
                                  style={'width': 105,
                                         'margin-left': '10px'},
                                  id='dropdown-time',
                                  clearable=False),
                      ],
                     className="d-grid gap-2 d-md-flex "
                               "justify-content-md-start",
                     ),
            html.H3(""),
            super().generate(presenter)])

    def set_callbacks(self, presenter):
        """
        Set the callbacks for the GUI.
        :param presenter: The presenter for the GUI.
        """
        super().set_callbacks(presenter)

        callback(Input('dropdown-time', 'value'))(presenter.set_state)
