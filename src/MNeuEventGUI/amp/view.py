from dash import Input, callback, dcc, html

from MNeuEventGUI.utils.batch_callback import dispatch
from MNeuEventGUI.view_template import ViewTemplate


class AmplitudeView(ViewTemplate):
    """
    A class for the view of the amplitude
    widget. This follows the MVP
    pattern.
    """
    def generate(self, presenter):
        """
        Creates the amplitude widget's GUI.
        :returns: the layout of the widget's
        GUI.
        """
        return html.Div([
            presenter._plot.layout,
            html.Div(['Amplitude threshold',
                      dcc.Input(id=presenter.component_id('Amp'),
                                value=0,
                                type='numeric')])
            ])

    def set_callbacks(self, presenter):
        """
        Set the callback for editing the amplitude.
        """
        super().set_callbacks(presenter)

        callback(Input(presenter.callback_id('Amp'), 'value'),
                 prevent_initial_call=True)(dispatch(presenter.edit_baseline))
