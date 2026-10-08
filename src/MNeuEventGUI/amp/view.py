from dash import Input, callback, dcc, html

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
                      dcc.Input(id='Amp',
                                value=0,
                                type='numeric')])
            ])

    def set_callbacks(self, presenter):
        """
        Set the callback for editing the amplitude.
        """
        super().set_callbacks(presenter)

        callback(Input('Amp', 'value'),
                 prevent_initial_call=True)(presenter.edit_baseline)
