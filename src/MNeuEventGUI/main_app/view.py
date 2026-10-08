import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, callback, dcc, html

from MNeuEventGUI.main_app.presenter import MainAppPresenter
from MNeuEventGUI.utils.errors import (
    DETAILS_BTN,
    DETAILS_COLLAPSE,
    display_error,
    error_alert,
    toggle_details,
)


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
                                                         dbc.icons.BOOTSTRAP],
                         on_error=display_error)

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
                    "MNeuEventGUI",
                    style={"textAlign": "center"},
                    className="mb-3"),

                # place the notifcations just under the title
                error_alert(),
                # ------------------------------------------------- #

                # this is also placed inside Loading, so it produces
                # a nice loading message when the GUI is busy.
                # The delay stops the spinner flashing on screen.
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
        several widgets write to the same table data, so the
        'allow_duplicate' option is used instead of the
        callback context (and a long if elif block).

        Errors are not returned by the callbacks, they are
        raised and then reported by the global error handler
        (see utils/errors.py).

        :param open_json: the function call for when the load
        filters button is pressed.
        :param save: the function call for when the one of the
        save buttons is pressed.

        """
        # Shows/hides the full error in the alert.
        callback([Output(DETAILS_COLLAPSE, 'is_open'),
                  Output(DETAILS_BTN, 'children')],
                 Input(DETAILS_BTN, 'n_clicks'),
                 State(DETAILS_COLLAPSE, 'is_open'),
                 prevent_initial_call=True)(toggle_details)

        # Updates the information on the loaded filter.
        callback([
                  Output('time-table', 'rowData', allow_duplicate=True),
                  Output('log-table', 'rowData', allow_duplicate=True),
                  Output('Amp', 'value', allow_duplicate=True),
                  Output('dropdown-time', 'value', allow_duplicate=True),
                  Output('time-table', 'columnDefs', allow_duplicate=True),],
                 Input('title_test', 'children'),
                 prevent_initial_call=True)(self.presenter.load_filter)

        # Plots the data after it is loaded.
        callback([Output('main_plot', 'figure'),
                  Output('time-table', 'rowData', allow_duplicate=True),
                  Output('time-table_add', 'disabled'),
                  Output('log-table', 'rowData', allow_duplicate=True),
                  Output('log-table_add', 'disabled'),
                  Output('time-table', 'columnDefs', allow_duplicate=True),
                  Output('amp_plot', 'figure')],
                 Input('file_name', 'children'),
                 [State('time-table', 'rowData'),
                  State('log-table', 'rowDara'),
                  State('debug', 'on')],
                 prevent_initial_call=True)(self.presenter.load_nxs)

        # Turns on debug mode
        callback(dash.dependencies.Input('debug', 'on'),
                 prevent_initial_call=True)(self.presenter.debug)

        # Saves the data (both histogram and filter file).
        callback(Output('save_exe_dummy', 'children'),
                 Input('save_btn_dummy', 'children'),
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
