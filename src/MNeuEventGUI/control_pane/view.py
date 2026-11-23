import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from MNeuEventGUI.log.presenter import LOG_TABLE
from MNeuEventGUI.plot_area.view import PLOT, TOOLTIP
from MNeuEventGUI.table.view import CHANGED_STATE
from MNeuEventGUI.time.presenter import TIME_TABLE
from MNeuEventGUI.time.view import DROPDOWN
from MNeuEventGUI.utils.batch import all_batches, batch_colour, batch_id
from MNeuEventGUI.utils.batch_callback import ordered_callback
from MNeuEventGUI.view_template import ViewTemplate

# the IDs for choosing the batch. The value of the
# dropdown is the key of the active batch.
ACTIVE = 'batch-select'
KEYS = 'batch-keys'
PREV = 'batch-prev'
NEXT = 'batch-next'
ADD_BATCH = 'batch-add'
REMOVE_BATCH = 'batch-remove'
SWATCH = 'batch-swatch'
PANES = 'batch-panes'
PANE = 'batch-pane'

HIDDEN = {'display': 'none'}


def icon_button(icon, component_id, title, disabled=False):
    """
    Creates a small button with an icon.
    :param icon: the bootstrap icon class
    :param component_id: the ID of the button
    :param title: the text shown when hovering on the button
    :param disabled: if the button starts disabled
    :returns: the button
    """
    return dbc.Button(html.I(className=icon),
                      id=component_id,
                      n_clicks=0,
                      color='link',
                      size='sm',
                      class_name='px-1',
                      title=title,
                      disabled=disabled)


class ControlPaneView(ViewTemplate):
    """
    Creates the main dash app for event filtering.
    """

    def generate(self, presenter):
        """
        Create the view for the app
        :param presenter: the presenter for the widget
        :returns: the app's view
        """

        # set width of the filter tables
        filter_width = 2

        # the batch is chosen with the back/forward buttons or
        # the dropdown (which can be searched), and only the
        # active batch's filters are shown
        active = presenter.batch_keys[0]
        (options, prev_disabled, next_disabled,
         remove_disabled, swatch) = presenter.batch_controls(
             active, presenter.batch_keys)
        controls = html.Div([
            icon_button('bi-chevron-left', PREV, 'Previous batch',
                        prev_disabled),
            html.Span(id=SWATCH, style=swatch),
            dcc.Dropdown(options,
                         active,
                         id=ACTIVE,
                         clearable=False,
                         searchable=True,
                         placeholder='Search batches',
                         style={'flex': '1 1 auto', 'minWidth': 0}),
            icon_button('bi-chevron-right', NEXT, 'Next batch',
                        next_disabled),
            icon_button('bi-plus-lg', ADD_BATCH, 'Add a batch'),
            icon_button('bi-trash', REMOVE_BATCH, 'Remove this batch',
                        remove_disabled),
            ],
                            className='d-flex align-items-center mb-2')

        batches = html.Div([
            dcc.Store(id=KEYS, data=presenter.batch_keys),
            controls,
            html.Div([self.pane(filter_presenter, index == 0)
                      for index, filter_presenter
                      in enumerate(presenter._filters)],
                     id=PANES),
            ])

        # setup the layout
        return dbc.Row([
                    dbc.Col(batches, width=filter_width),
                    dbc.Col(presenter._plot.layout, width=12-filter_width)
                    ],
                        className="g-0", align='center')

    @staticmethod
    def swatch_style(index):
        """
        :param index: the index of the active batch
        :returns: the style of the mark showing the
        active batch's colour (as used in the plot)
        """
        return {'backgroundColor': batch_colour(index),
                'width': '0.75rem',
                'height': '0.75rem',
                'borderRadius': '50%',
                'flex': '0 0 auto',
                'marginRight': '0.25rem'}

    @staticmethod
    def pane_style(shown):
        """
        :param shown: if the batch's filters are shown
        :returns: the style for a batch's filters
        """
        return None if shown else HIDDEN

    def pane(self, filter_presenter, active):
        """
        Creates the filters for a batch.
        :param filter_presenter: the batch's filter presenter
        :param active: if the batch is the active one
        :returns: the tab's contents
        """
        return html.Div(filter_presenter.layout,
                        id=batch_id(PANE, filter_presenter.key),
                        key=str(filter_presenter.key),
                        style=self.pane_style(active))

    def set_callbacks(self, presenter):
        """
        Set the callbacks for the widget
        :param pressenter: the presenter for the widget
        """
        self.set_tab_callbacks(presenter)

        order = presenter.order
        plot = presenter._plot.component_id(PLOT)
        tooltip = presenter._plot.component_id(TOOLTIP)

        # the filter type is picked up from the model, so we trigger
        # off the time table's changed state signal. Using the dropdown
        # directly would race with the callback that updates the model.
        ordered_callback(order,
                         Output(plot, 'figure', allow_duplicate=True),
                         [Input(all_batches(TIME_TABLE), 'rowData'),
                          Input(all_batches(LOG_TABLE), 'rowData'),
                          Input(all_batches(TIME_TABLE + CHANGED_STATE),
                                'data'),
                          Input(ACTIVE, 'value'),
                          Input(KEYS, 'data')],
                         prevent_initial_call=True)(presenter.make_plot)

        ordered_callback(order,
                         [Output(tooltip, 'show', allow_duplicate=True),
                          Output(tooltip, 'bbox', allow_duplicate=True),
                          Output(tooltip, 'children', allow_duplicate=True)],
                         [Input(plot, 'hoverData')],
                         [State(all_batches(TIME_TABLE), 'rowData'),
                          State(all_batches(TIME_TABLE + DROPDOWN), 'value')],
                         prevent_initial_call=True)(presenter.display_hover)

        # calculating updates the number of events for every batch
        ordered_callback(order,
                         Output(all_batches('N_events'), 'children',
                                allow_duplicate=True),
                         [Input(all_batches('calc_btn'), 'n_clicks')],
                         prevent_initial_call=True)(presenter.calculate)

    def set_tab_callbacks(self, presenter):
        """
        Sets the callbacks for choosing, adding and
        removing batches.
        :param presenter: the presenter for the widget
        """
        order = presenter.order

        # show the active batch's filters
        ordered_callback(order,
                         Output(all_batches(PANE), 'style'),
                         [Input(ACTIVE, 'value')],
                         prevent_initial_call=True)(presenter.show_batch)

        # the dropdown options and buttons depend on which batch is
        # active and on the batches (the labels follow the index, so
        # they change when an earlier batch is removed)
        callback([Output(ACTIVE, 'options'),
                  Output(PREV, 'disabled'),
                  Output(NEXT, 'disabled'),
                  Output(REMOVE_BATCH, 'disabled'),
                  Output(SWATCH, 'style')],
                 [Input(ACTIVE, 'value'),
                  Input(KEYS, 'data')],
                 prevent_initial_call=True)(presenter.batch_controls)

        callback(Output(ACTIVE, 'value', allow_duplicate=True),
                 Input(PREV, 'n_clicks'),
                 State(ACTIVE, 'value'),
                 prevent_initial_call=True)(presenter.previous_batch)

        callback(Output(ACTIVE, 'value', allow_duplicate=True),
                 Input(NEXT, 'n_clicks'),
                 State(ACTIVE, 'value'),
                 prevent_initial_call=True)(presenter.next_batch)

        callback([Output(PANES, 'children', allow_duplicate=True),
                  Output(ACTIVE, 'value', allow_duplicate=True),
                  Output(KEYS, 'data', allow_duplicate=True)],
                 Input(ADD_BATCH, 'n_clicks'),
                 prevent_initial_call=True)(presenter.add_batch)

        callback([Output(PANES, 'children', allow_duplicate=True),
                  Output(ACTIVE, 'value', allow_duplicate=True),
                  Output(KEYS, 'data', allow_duplicate=True)],
                 Input(REMOVE_BATCH, 'n_clicks'),
                 State(ACTIVE, 'value'),
                 prevent_initial_call=True)(presenter.remove_batch)

    def hover_text(self, pt, lines):
        """
        A method to generate the text for the tooltip
        (hover text).
        :param pt: the information about the point being hovered on
        :param lines: the status text for each batch
        :returns: An updated layout for the tooltip
        """
        children = html.Div([
            html.H5('Data Point'),
            html.P(f"x: {pt['x']:.3f},  y: {pt['y']:.3f}"),
            html.H5('Status'),
            *[html.P(line) for line in lines]
            ])
        return children
