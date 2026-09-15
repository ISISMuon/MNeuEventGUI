from MuonDataLib.GUI.main_app.presenter import MainAppPresenter

import dash
from dash import Dash, Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc


class MainApp(Dash):
    """
    Creates the main dash app for event filtering.
    """
    def __init__(self, open_nxs, open_json, save):
        """
        Creates the Dash app.
        This is in the MVP style,
        except this is the widget that needs
        to be called to activate it.

        :param open_nxs: the function call for when the load
        button is pressed.
        :param open_json: the function call for when the load
        filters button is pressed.
        :param save: the function call for when the one of the
        save buttons is pressed.
        """
        super().__init__(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,
                                                         dbc.icons.BOOTSTRAP])

        self.N_submit = 0
        self.presenter = MainAppPresenter(open_nxs)
        self.layout = self.generate()
        self.set_callbacks(open_json, save)

    def generate(self):
        """
        Create the view for the app
        :returns: the app's view
        """

        # setup the layout
        return dbc.Container(
            [
                html.H1(
                    "MuonDataGUI",
                    style={"textAlign": "center"},
                    className="mb-3"),

                # place the notifcations just under the title
                dbc.Alert([html.H4("   ERROR MESSAGE",
                                   className='bi-x-octagon-fill'),
                           html.P("Error", id='error_msg')],
                          id='error',
                          dismissable=True,
                          fade=False,
                          color='danger',
                          is_open=False),
                # ------------------------------------------------- #

                # this is also placed inside Loading, so it produces
                # a nice loading message when the GUI is busy.
                # The delay stops the spinner flashing on screan.
                dcc.Loading([self.presenter.load.layout,
                             self.presenter.control.layout,
                             self.presenter.save.layout,
                             ],
                            overlay_style={"visibility": "visible",
                                           "opacity": .5,
                                           "backgroundColor": "white"},
                            custom_spinner=html.H2(["Please wait ... ",
                                                    dbc.Spinner(color="danger")
                                                    ],
                                                   className='bi-hourglass'
                                                             '-split'
                                                             ' me-md-2',
                                                   id='spinner'),
                            delay_show=50),

                ],
            fluid=True,
        )

    def set_callbacks(self, open_json, save):
        """
        A method to setup all of the callbacks needed
        by the GUI.

        Callbacks should all have unique Output's. However,
        we want several things to be able to return an
        error message. Instead of using the callback
        context to determine what was called (and a long
        if elif block) it was decided to use the
        'allow_duplicate' option instead.

        :param open_json: the function call for when the load
        filters button is pressed.
        :param save: the function call for when the one of the
        save buttons is pressed.

        """
        # opens the error notifcation if the error message changes
        callback(Output('error', 'is_open'),
                 Input('error_msg', 'children'),
                 prevent_initial_call=True)(self.presenter.alert)

        # Updates the information on the loaded filter. With error
        # catching.
        callback([
                  Output('time-table', 'rowData', allow_duplicate=True),
                  Output('log-table', 'rowData', allow_duplicate=True),
                  Output('Amp', 'value', allow_duplicate=True),
                  Output('min-time', 'value', allow_duplicate=True),
                  Output('max-time', 'value', allow_duplicate=True),
                  Output('num-bin', 'value', allow_duplicate=True),
                  Output('dropdown-time', 'value', allow_duplicate=True),
                  Output('time-table', 'columnDefs', allow_duplicate=True),
                  Output('error_msg', 'children', allow_duplicate=True)],
                 Input('title_test', 'children'),
                 State('debug', 'on'),
                 prevent_initial_call=True)(self.presenter.load_filter)

        # Plots the data after it is loaded.
        callback([Output('main_plot', 'figure'),
                  Output('time-table', 'rowData', allow_duplicate=True),
                  Output('time-table_add', 'disabled'),
                  Output('log-table', 'rowData', allow_duplicate=True),
                  Output('log-table_add', 'disabled'),
                  Output('time-table', 'columnDefs', allow_duplicate=True),
                  Output('amp_plot', 'figure'),
                  Output('error_msg', 'children', allow_duplicate=True)],
                 Input('file_name', 'children'),
                 [State('time-table', 'rowData'),
                  State('log-table', 'rowDara'),
                  State('debug', 'on')],
                 prevent_initial_call=True)(self.presenter.load_nxs)

        # Turns on debug mode
        callback(dash.dependencies.Input('debug', 'on'),
                 prevent_initial_call=True)(self.presenter.debug)

        # Saves the data (both histogram and filter file).
        callback([Output('save_exe_dummy', 'children'),
                  Output('error_msg', 'children', allow_duplicate=True)],
                 Input('save_btn_dummy', 'children'),
                 [State('time-table', 'rowData'),
                  State('dropdown-time', 'value'),
                  State('log-table', 'rowData'),
                  State('Amp', 'value'),
                  # histogram settings
                  State('min-time', 'value'),
                  State('max-time', 'value'),
                  State('num-bin', 'value'),
                  State('debug', 'on')],
                 prevent_initial_call=True)(self.presenter.save_data)

        callback([Output('load_confirm', 'displayed'),
                  Output('load_confirm', 'submit_n_clicks')],
                 Input('Load', 'n_clicks'),
                 [State('time-table', 'rowData'),
                  State('load_confirm', 'submit_n_clicks')],
                 prevent_initial_call=True)(self.presenter.confirm_load)

        """
        callbacks from pyqt
        """
        # open a nxs file
        callback(
                 Output('file_name', 'children'),
                 Input('load_confirm', 'submit_n_clicks'),
                 State('file_name', 'children'),
                 prevent_initial_call=True)(self.presenter.open_nxs)

        # open a json filter file
        callback(
                 Output('title_test', 'children'),
                 Input('load_filters', 'n_clicks'),
                 prevent_initial_call=True)(open_json)

        # open file browser on save (nxs and json)
        callback(
                 Output('save_btn_dummy', 'children'),
                 [Input('Save', 'n_clicks'),
                  Input('save_filters', 'n_clicks')],
                 prevent_initial_call=True)(save)
