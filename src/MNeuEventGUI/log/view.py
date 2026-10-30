import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from MNeuEventGUI.plot_area.view import PLOT
from MNeuEventGUI.table.view import ADD, TableView


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
        _id = presenter.component_id
        text = html.Div([html.H4('Sample log:'),
                         dcc.Dropdown(['Temp'],
                                      'Temp',
                                      id=_id('_selection'),
                                      clearable=False),
                         html.Hr(),
                         html.H4('Statistics'),
                         html.P('max: 0.0', id=_id('_max')),
                         html.P('mean: 0.0', id=_id('_mean')),
                         html.P('min: 0.0', id=_id('_min')),
                         html.Hr(),
                         html.P('sigma (std): 0.0', id=_id('_std')),
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
                                    id=presenter.component_id('_ok'),
                                    n_clicks=0,
                                    className='ms-auto'),
                         dbc.Button('cancel',
                                    color='secondary',
                                    n_clicks=0,
                                    id=presenter.component_id('_cancel'),
                                    className='ms-md-2')])

        return html.Div([
            # make pop up
            dbc.Modal(
                [dbc.ModalHeader(dbc.ModalTitle('Sample log selection'),
                                 close_button=False),
                 dbc.ModalBody(tmp),
                 dbc.ModalFooter(btns)],
                id=presenter.component_id('_selector'),
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

        table = presenter.component_id()
        callback([Output(presenter._plot.component_id(PLOT), 'figure',
                         allow_duplicate=True),
                  Output(presenter.component_id('_max'), 'children'),
                  Output(presenter.component_id('_mean'), 'children'),
                  Output(presenter.component_id('_min'), 'children'),
                  Output(presenter.component_id('_std'), 'children'),],
                 Input(presenter.component_id('_selection'), 'value'),
                 prevent_initial_call=True)(presenter.show_log_data)

        callback([Output(presenter.component_id('_selector'), 'is_open'),
                  Output(table, 'rowData', allow_duplicate=True)],
                 [Input(presenter.component_id('_ok'), 'n_clicks'),
                  Input(presenter.component_id('_cancel'), 'n_clicks')],
                 [State(presenter.component_id('_selection'), 'value'),
                  State(table, 'virtualRowData')],
                 prevent_initial_call=True)(presenter.close_modal)

        callback([
                  Output(presenter.component_id('_selection'), 'options'),
                  Output(presenter.component_id('_selection'), 'value')],
                 Input(presenter.component_id('_selector'), 'is_open'),
                 State(table, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.select_log)

    def set_add_callback(self, presenter):
        """
        This sets the add callback, it needs to be
        different to the TableView version as we want
        to have the pop up appear and not just add a row.
        :param presenter: the presenter object
        """
        callback(Output(presenter.component_id('_selector'), 'is_open',
                        allow_duplicate=True),
                 Input(presenter.component_id(ADD), 'n_clicks'),
                 State(presenter.component_id(), 'virtualRowData'),
                 prevent_initial_call=True)(presenter.add)

    def set_btn_callback(self, presenter):
        """
        This sets the response of any button being pressed in the
        table. This needs to be different because we have 2 buttons
        in the sample log table (delete and to create the pop up)
        :param presenter: the presenter object
        """
        table = presenter.component_id()
        callback([Output(table, "rowData", allow_duplicate=True),
                  Output(presenter.component_id('_selector'), 'is_open',
                         allow_duplicate=True)],
                 Input(table, "cellRendererData"),
                 State(table, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.btn_pressed)
