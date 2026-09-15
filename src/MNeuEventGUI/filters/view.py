from MuonDataLib.GUI.view_template import ViewTemplate
from dash import html
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, State


NUM = 'Number of events: '
NC = 'Not Calculated'


class FilterView(ViewTemplate):
    """
    A class for the view of the filter
    widget. This follows the MVP
    pattern.
    """

    def generate(self, presenter):
        """
        Creates the filter widget's GUI.
        :param presenter: the presenter for the widget
        :returns: the layout of the widget's
        GUI.
        """
        return html.Div([
            html.P("Title: testing", id='title_test',
                   hidden=True),
            dbc.Accordion([
                dbc.AccordionItem(
                    [presenter._time.layout],
                    title="Time filters"),
                dbc.AccordionItem(
                    [presenter._log.layout],
                    title="Sample Log filters"),
                dbc.AccordionItem(
                    [presenter._amp.layout],
                    title="Amplitude filter"),
                dbc.AccordionItem(
                    [presenter._hist_settings.layout],
                    title="Histogram settings"),
                ],
                         start_collapsed=True),
            dbc.Button('Calculate',
                       id='calc_btn',
                       color='primary',
                       className='me-md-2'),
            html.P(self.no_events_str, id='N_events'),
            ])

    def set_callbacks(self, presenter):
        """
        Sets the callbacks for the widget
        :param presenter: the presenter for the widget
        """
        # calculate events when Calculate button is pressed
        callback([Output('N_events', 'children'),
                  Output('error_msg', 'children', allow_duplicate=True)],
                 Input('calc_btn', 'n_clicks'),
                 [State('time-table', 'rowData'),
                  State('dropdown-time', 'value'),
                  State('log-table', 'rowData'),
                  State('Amp', 'value'),
                  State('min-time', 'value'),
                  State('max-time', 'value'),
                  State('num-bin', 'value'),],
                 prevent_initial_call=True)(presenter.calculate)

        # show filename if filter data is equal to that in the file
        callback(Output('title_test', 'hidden'),
                 [Input('title_test', 'children'),
                  Input('time-table', 'rowData'),
                  Input('log-table', 'rowData'),
                  Input('Amp', 'value'),
                  Input('min-time', 'value'),
                  Input('max-time', 'value'),
                  Input('num-bin', 'value'),
                  ],
                 prevent_initial_call=True)(presenter.show_file)

        # clear events string if event data is made invalid
        callback(Output('N_events', 'children', allow_duplicate=True),
                 [Input('time-table_changed_state', 'data'),
                  Input('Amp', 'value'),
                  Input('time-table_add', 'n_clicks'),
                  Input('log-table_add', 'n_clicks'),
                  Input('time-table', 'cellRendererData'),
                  Input('log-table', 'cellRendererData')],
                 prevent_initial_call=True)(lambda *_: self.no_events_str)

        # clear events string if time filter parameters change
        callback(Output('N_events', 'children', allow_duplicate=True),
                 Input('time-table', 'cellValueChanged'),
                 State('N_events', 'children'),
                 prevent_initial_call=True)(presenter.update_N_events)

        # clear events string if log filter parameters change
        callback(Output('N_events', 'children', allow_duplicate=True),
                 Input('log-table', 'cellValueChanged'),
                 State('N_events', 'children'),
                 prevent_initial_call=True)(presenter.update_N_events)

    @property
    def no_events_str(self):
        """
        Get the string for no events to display
        :returns: the string for no events
        """
        return NUM + NC

    def get_N(self, N):
        """
        Gets the updated GUI componenet for the
        number of events.
        :param N: the number of events
        """
        return html.P(NUM + str(N))
