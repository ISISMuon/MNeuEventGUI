from MuonDataLib.GUI.view_template import ViewTemplate
from dash import html, dcc


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
        Sets the callbacks for the GUI.
        :param presenter: the presenter object
        """
        super().set_callbacks(presenter)
