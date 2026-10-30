import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from MNeuEventGUI.view_template import ViewTemplate


class TableView(ViewTemplate):
    """
    A class for the view of a
    table. This follows the MVP
    pattern.
    """
    def generate(self, presenter):
        """
        Creates the table widget's GUI.
        :param presenter: the presenter for the GUI
        :returns: the layout of the widget's
        GUI.
        """
        return html.Div([
            dbc.Button(id=presenter.component_id('_add'),
                       class_name='bi-plus-lg',
                       disabled=True),
            dcc.Store(data=False, id=presenter.component_id('_changed_state')),
            dag.AgGrid(id=presenter.component_id(),
                       columnDefs=presenter.cols.get_column_dict,
                       rowData=[],
                       defaultColDef={'editable': True,
                                      'suppressMovable': True},
                       ),
            html.Div(id=presenter.component_id('-dropdown-container'))
            ])

    def set_callbacks(self, presenter):
        """
        Set the callbacks for the GUI.
        :param presenter: the presenter for the GUI
        """
        table = presenter.component_id()
        callback(Output(table, 'rowData', allow_duplicate=True),
                 Input(table, 'cellValueChanged'),
                 State(table, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.validate)

        callback(Output(table, 'rowData', allow_duplicate=True),
                 Input(table, 'cellValueChanged'),
                 State(table, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.edit_row)

        self.set_btn_callback(presenter)
        self.set_add_callback(presenter)

    def set_btn_callback(self, presenter):
        """
        A callback for pressing the button within the table.
        This is so we can easily overwrite it if there are
        multiple buttons in the table. As its not possible to
        distinguish between the signals.
        :param presenter: the presenter object
        """
        table = presenter.component_id()
        callback(Output(table, "rowData", allow_duplicate=True),
                 Input(table, "cellRendererData"),
                 State(table, 'virtualRowData'),
                 prevent_initial_call=True)(presenter.delete_row)

    def set_add_callback(self, presenter):
        """
        Sets a callback for the add button. This is so we
        can overwrite it if we need to.
        :param presenter: the presenter object
        """
        callback(Output(presenter.component_id(), 'rowData',
                        allow_duplicate=True),
                 Input(presenter.component_id('_add'), 'n_clicks'),
                 prevent_initial_call=True)(lambda _: presenter.add())
