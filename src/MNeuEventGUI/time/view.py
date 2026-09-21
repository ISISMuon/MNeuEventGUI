from dash import dcc, html

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
                     dcc.Dropdown(['Exclude', 'Include'],
                                  'Exclude',
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

