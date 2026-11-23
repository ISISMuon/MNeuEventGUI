from dash import Input, Output, State, callback, dcc, html

from MNeuEventGUI.table.view import CHANGED_STATE, TableView
from MNeuEventGUI.utils.batch_callback import dispatch

# suffix for the ID of the filter type dropdown
DROPDOWN = '_dropdown'


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
                     dcc.Dropdown(['Include', 'Exclude'],
                                  'Include',
                                  style={'width': 105,
                                         'margin-left': '10px'},
                                  id=presenter.component_id(DROPDOWN),
                                  clearable=False),
                      ],
                     className="d-grid gap-2 d-md-flex "
                               "justify-content-md-start",
                     ),
            html.H3(""),
            super().generate(presenter)])

    def set_callbacks(self, presenter):
        """
        Set the callbacks for the GUI.
        :param presenter: The presenter for the GUI.
        """
        super().set_callbacks(presenter)

        # update the model and tell the rest of the GUI about it.
        # Anything that depends on the filter type should use the
        # changed state signal, so that it cannot read the model
        # before it has been updated.
        callback([Output(presenter.callback_id(), 'columnDefs',
                         allow_duplicate=True),
                  Output(presenter.callback_id(CHANGED_STATE), 'data')],
                 Input(presenter.callback_id(DROPDOWN), 'value'),
                 State(presenter.callback_id(CHANGED_STATE), 'data'),
                 prevent_initial_call=True)(dispatch(presenter.update_state))
