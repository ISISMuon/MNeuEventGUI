import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from MNeuEventGUI.log.presenter import LOG_TABLE
from MNeuEventGUI.plot_area.view import PLOT, TOOLTIP
from MNeuEventGUI.table.view import CHANGED_STATE
from MNeuEventGUI.time.presenter import TIME_TABLE
from MNeuEventGUI.time.view import DROPDOWN
from MNeuEventGUI.utils.batch import (
    all_batches,
    batch_colour,
    batch_id,
    batch_label,
)
from MNeuEventGUI.utils.batch_callback import ordered_callback, triggered_batch
from MNeuEventGUI.view_template import ViewTemplate

# the IDs for the batch tabs
ACTIVE = 'batch-tabs'
KEYS = 'batch-keys'
NAV = 'batch-nav'
PANES = 'batch-panes'
ADD_BATCH = 'batch-add'
LINK = 'batch-link'
LABEL = 'batch-label'
CLOSE = 'batch-close'
PANE = 'batch-pane'

HIDDEN = {'display': 'none'}


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

        # a tab of filters for each batch. The tabs are made
        # by hand, because a dbc.Tab's label can only be text
        # and each tab needs a button to remove it.
        active = presenter.batch_keys[0]
        n_batches = len(presenter._filters)
        tabs = html.Div([
            dcc.Store(id=ACTIVE, data=active),
            dcc.Store(id=KEYS, data=presenter.batch_keys),
            html.Div([
                dbc.Nav([self.nav_item(filter_presenter, index,
                                       index == 0, n_batches)
                         for index, filter_presenter
                         in enumerate(presenter._filters)],
                        id=NAV,
                        class_name='nav-tabs flex-wrap flex-grow-1'),
                # this is not one of the tabs, as Dash re-triggers
                # the callbacks of components in the tabs when they
                # are changed
                dbc.Button(html.I(className='bi-plus-lg'),
                           id=ADD_BATCH,
                           n_clicks=0,
                           color='link',
                           size='sm',
                           title='Add a batch'),
                ],
                     className='d-flex align-items-end mb-2'),
            html.Div([self.pane(filter_presenter, index == 0)
                      for index, filter_presenter
                      in enumerate(presenter._filters)],
                     id=PANES),
            ])

        # setup the layout
        return dbc.Row([
                    dbc.Col(tabs, width=filter_width),
                    dbc.Col(presenter._plot.layout, width=12-filter_width)
                    ],
                        className="g-0", align='center')

    @staticmethod
    def link_style(index):
        """
        :param index: the index of the batch
        :returns: the style for the batch's tab
        """
        return {'color': batch_colour(index), 'fontWeight': 'bold'}

    @staticmethod
    def close_style(n_batches):
        """
        :param n_batches: the number of batches
        :returns: the style of the buttons that remove a batch,
        which are hidden when there is only one batch
        """
        return HIDDEN if n_batches == 1 else {'cursor': 'pointer'}

    def nav_item(self, filter_presenter, index, active, n_batches):
        """
        Creates the tab for a batch.
        :param filter_presenter: the batch's filter presenter
        :param index: the index of the batch
        :param active: if the batch is the active one
        :param n_batches: the number of batches
        :returns: the tab
        """
        key = filter_presenter.key
        return dbc.NavItem([
            dbc.NavLink(html.Span(batch_label(index),
                                  id=batch_id(LABEL, key)),
                        id=batch_id(LINK, key),
                        n_clicks=0,
                        class_name='px-2',
                        active=active,
                        style=self.link_style(index)),
            # this is beside the link, not in it, so that
            # removing a batch does not also select it
            html.I(id=batch_id(CLOSE, key),
                   className='bi-x',
                   n_clicks=0,
                   title='Remove this batch',
                   style=self.close_style(n_batches)),
            ],
                           className='d-flex align-items-center',
                           # React matches the tabs by key, not by position,
                           # so removing a tab does not reuse (and re-trigger)
                           # the components of the tabs after it
                           key=str(key))

    @staticmethod
    def pane_style(shown):
        """
        :param shown: if the tab's contents are shown
        :returns: the style for a batch's tab contents
        """
        return None if shown else HIDDEN

    def pane(self, filter_presenter, active):
        """
        Creates the contents of the tab for a batch.
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
                          Input(ACTIVE, 'data'),
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
        Sets the callbacks for selecting, adding and
        removing batches.
        :param presenter: the presenter for the widget
        """
        order = presenter.order

        def select(_):
            return presenter.select_batch(*triggered_batch())

        callback(Output(ACTIVE, 'data', allow_duplicate=True),
                 Input(all_batches(LINK), 'n_clicks'),
                 prevent_initial_call=True)(select)

        # show the active batch's tab
        ordered_callback(order,
                         [Output(all_batches(PANE), 'style'),
                          Output(all_batches(LINK), 'active')],
                         [Input(ACTIVE, 'data')],
                         prevent_initial_call=True)(presenter.show_batch)

        callback([Output(NAV, 'children', allow_duplicate=True),
                  Output(PANES, 'children', allow_duplicate=True),
                  Output(ACTIVE, 'data', allow_duplicate=True),
                  Output(KEYS, 'data', allow_duplicate=True)],
                 Input(ADD_BATCH, 'n_clicks'),
                 prevent_initial_call=True)(presenter.add_batch)

        def remove(_, active):
            key, _ = triggered_batch()
            return presenter.remove_batch(key, active)

        callback([Output(NAV, 'children', allow_duplicate=True),
                  Output(PANES, 'children', allow_duplicate=True),
                  Output(ACTIVE, 'data', allow_duplicate=True),
                  Output(KEYS, 'data', allow_duplicate=True)],
                 Input(all_batches(CLOSE), 'n_clicks'),
                 State(ACTIVE, 'data'),
                 prevent_initial_call=True)(remove)

        # the labels and colours follow the batch index,
        # so they change when an earlier batch is removed
        ordered_callback(order,
                         [Output(all_batches(LABEL), 'children'),
                          Output(all_batches(LINK), 'style'),
                          Output(all_batches(CLOSE), 'style')],
                         [Input(KEYS, 'data')],
                         prevent_initial_call=True)(presenter.relabel)

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
