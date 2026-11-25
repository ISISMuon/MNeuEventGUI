import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from MNeuEventGUI.table.view import ADD, CHANGED_STATE
from MNeuEventGUI.time.view import DROPDOWN
from MNeuEventGUI.utils.batch import ACTIVE, NUM_BATCHES
from MNeuEventGUI.view_template import ViewTemplate

# the ID of the filter widget
FILTERS = 'filters'
# the ID of the store for the name of a filter file to load
FILTER_FILE = 'filter_file'

NUM = 'Events in this batch: '
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
        return html.Div(id=presenter.component_id(FILTERS), children=[
            dcc.Store(id=FILTER_FILE),
            html.P("",
                   id=presenter.component_id('title_test'),
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
                       id=presenter.component_id('calc_btn'),
                       color='primary',
                       className='me-md-2'),
            html.P(self.no_events_str,
                   id=presenter.component_id('N_events')),
            ])

    def set_callbacks(self, presenter):
        """
        Sets the callbacks for the widget. The widgets
        show the active batch, so callbacks that change
        a batch are given the active batch's index.
        :param presenter: the presenter for the widget
        """
        title = presenter.component_id('title_test')
        n_events = presenter.component_id('N_events')
        time_table = presenter._time.component_id()
        log_table = presenter._log.component_id()
        amp = presenter.component_id('Amp')
        min_time = presenter.component_id('min-time')
        max_time = presenter.component_id('max-time')
        num_bins = presenter.component_id('num-bins')
        active = State(ACTIVE, 'value')

        # the widgets for the filters and settings, then the
        # filter file name and the number of events
        widgets = [Output(time_table, 'rowData', allow_duplicate=True),
                   Output(log_table, 'rowData', allow_duplicate=True),
                   Output(amp, 'value', allow_duplicate=True),
                   Output(presenter._time.component_id(DROPDOWN), 'value',
                          allow_duplicate=True),
                   Output(min_time, 'value', allow_duplicate=True),
                   Output(max_time, 'value', allow_duplicate=True),
                   Output(num_bins, 'value', allow_duplicate=True),
                   Output(time_table, 'columnDefs', allow_duplicate=True),
                   Output(title, 'children', allow_duplicate=True),
                   Output(n_events, 'children', allow_duplicate=True)]

        # show the active batch, when it changes or a batch is
        # added or removed
        callback(widgets,
                 [Input(ACTIVE, 'value'),
                  Input(NUM_BATCHES, 'data')],
                 prevent_initial_call=True)(presenter.fill)

        # load a filter file into the active batch
        callback(widgets,
                 Input(FILTER_FILE, 'data'),
                 active,
                 prevent_initial_call=True)(presenter.load_filter_file)

        # show filename if filter data is equal to that in the file
        callback(Output(title, 'hidden'),
                 [Input(title, 'children'),
                  Input(time_table, 'rowData'),
                  Input(log_table, 'rowData'),
                  Input(amp, 'value'),
                  Input(min_time, 'value'),
                  Input(max_time, 'value'),
                  Input(num_bins, 'value'),
                  ],
                 active,
                 prevent_initial_call=True)(presenter.show_file)

        # calculate the number of events (for every batch)
        callback(Output(n_events, 'children', allow_duplicate=True),
                 Input(presenter.component_id('calc_btn'), 'n_clicks'),
                 active,
                 prevent_initial_call=True)(presenter.calculate)

        # update the data with the amplitude and histogram settings.
        # These are also set when the active batch is shown, so they
        # only clear the number of events if the batch has changed.
        callback(Output(n_events, 'children', allow_duplicate=True),
                 Input(amp, 'value'),
                 active,
                 prevent_initial_call=True)(presenter.edit_amp)

        callback(Output(n_events, 'children', allow_duplicate=True),
                 [Input(min_time, 'value'),
                  Input(max_time, 'value'),
                  Input(num_bins, 'value')],
                 active,
                 prevent_initial_call=True)(presenter.edit_hist_settings)

        # clear events string if event data is made invalid
        callback(Output(n_events, 'children', allow_duplicate=True),
                 [Input(presenter._time.component_id(CHANGED_STATE),
                        'data'),
                  Input(presenter._time.component_id(ADD), 'n_clicks'),
                  Input(presenter._log.component_id(ADD), 'n_clicks'),
                  Input(time_table, 'cellRendererData'),
                  Input(log_table, 'cellRendererData')],
                 active,
                 prevent_initial_call=True
                 )(lambda *args: presenter.uncount(args[-1]))

        # clear events string if filter parameters change
        for table in (time_table, log_table):
            callback(Output(n_events, 'children', allow_duplicate=True),
                     Input(table, 'cellValueChanged'),
                     [State(n_events, 'children'),
                      active],
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
