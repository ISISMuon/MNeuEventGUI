from MuonDataLib.GUI.table.view import TableView
from dash import html, dcc
from dash import Input, Output, callback, State


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
            dcc.ConfirmDialog(
                              id='confirm-time',
                              message='This will clear all of the filters. '
                                      'If you want to keep them, you should '
                                      'save the filters first. '
                                      'Are you sure you want to continue?',
                              submit_n_clicks_timestamp=0,
                              cancel_n_clicks_timestamp=0
                              ),
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

    def set_callbacks(self, presenter):
        super().set_callbacks(presenter)

        callback([Output('confirm-time', 'displayed'),
                  Output('time-table', 'columnDefs')],
                 Input('dropdown-time', 'value'),
                 State('time-table', 'rowData'),
                 prevent_initial_call=True)(presenter.display_confirm)

        callback([Output('dropdown-time', 'value'),
                  Output('time-table', 'rowData', allow_duplicate=True),
                  Output('time-table', 'columnDefs', allow_duplicate=True),
                  Output('time-table_changed_state', 'data')
                  ],
                 [Input('confirm-time', 'submit_n_clicks_timestamp'),
                  Input('confirm-time', 'cancel_n_clicks_timestamp')],
                 State('dropdown-time', 'value'),
                 State('time-table', 'rowData'),
                 prevent_initial_call=True)(presenter.confirm)
