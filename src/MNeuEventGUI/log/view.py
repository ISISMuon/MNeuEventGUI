from MuonDataLib.GUI.table.view import TableView
from dash import html, dcc
from dash import Input, Output, State, callback
import dash_bootstrap_components as dbc


class LogView(TableView):
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

        # set up the selection and stats (text area)
        text = html.Div([html.H4('Sample log:'),
                         dcc.Dropdown(['Temp'],
                                      'Temp',
                                      id='log_selection',
                                      clearable=False),
                         html.Hr(),
                         html.H4('Statistics'),
                         html.P('max: 0.0', id='log_max'),
                         html.P('mean: 0.0', id='log_mean'),
                         html.P('min: 0.0', id='log_min'),
                         html.Hr(),
                         html.P('sigma (std): 0.0', id='log_std'),
                         ])
        # set width of the text area
        filter_width = 4

        # setup the layout (text area + plot area)
        tmp = dbc.Row([dbc.Col(text, width=filter_width),
                       dbc.Col(presenter._plot.layout, width=12-filter_width)],
                      className="g-0", align='center')

        # setup the ok and cancel buttons at bottom of the pop up
        btns = html.Div([dbc.Button('ok',
                                    color='secondary',
                                    id='log_ok',
                                    n_clicks=0,
                                    className='ms-auto'),
                         dbc.Button('cancel',
                                    color='secondary',
                                    n_clicks=0,
                                    id='log_cancel',
                                    className='ms-md-2')])

        return html.Div([
            # make pop up
            dbc.Modal(
                [dbc.ModalHeader(dbc.ModalTitle('Sample log selection'),
                                 close_button=False),
                 dbc.ModalBody(tmp),
                 dbc.ModalFooter(btns)],
                id='log_selector',
                size='xl',
                is_open=False),
            # setup normal table
            super().generate(presenter)])

    def set_callbacks(self, presenter):
        """
        Sets the callbacks for the GUI.
        Have additional callbacks for:
        - updating the data in the pop up
        - closing the pop up
        - setting the combo box options and value when
        opening the pop up
        :param presenter: the presenter object
        """
        super().set_callbacks(presenter)

        callback([Output('log_plot', 'figure', allow_duplicate=True),
                  Output('log_max', 'children'),
                  Output('log_mean', 'children'),
                  Output('log_min', 'children'),
                  Output('log_std', 'children'),],
                 Input('log_selection', 'value'),
                 prevent_initial_call=True)(presenter.show_log_data)

        callback([Output('log_selector', 'is_open'),
                  Output(presenter.ID, 'rowData', allow_duplicate=True)],
                 [Input('log_ok', 'n_clicks'),
                  Input('log_cancel', 'n_clicks')],
                 [State('log_selection', 'value'),
                  State(presenter.ID, 'virtualRowData')],
                 prevent_initial_call=True)(presenter.close_modal)

        callback([
                  Output('log_selection', 'options'),
                  Output('log_selection', 'value')],
                 Input('log_selector', 'is_open'),
                 State(presenter.ID, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.select_log)

    def set_add_callback(self, presenter):
        """
        This sets the add callback, it needs to be
        different to the TableView version as we want
        to have the pop up appear and not just add a row.
        :param presenter: the presenter object
        """
        callback(Output('log_selector', 'is_open', allow_duplicate=True),
                 Input(presenter.ID + '_add', 'n_clicks'),
                 State(presenter.ID, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.add)

    def set_btn_callback(self, presenter):
        """
        This sets the response of any button being pressed in the
        table. This needs to be different because we have 2 buttons
        in the sample log table (delete and to create the pop up)
        :param presenter: the presenter object
        """
        callback([Output(presenter.ID, "rowData", allow_duplicate=True),
                  Output('log_selector', 'is_open', allow_duplicate=True)],
                 Input(presenter.ID, "cellRendererData"),
                 State(presenter.ID, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.btn_pressed)
