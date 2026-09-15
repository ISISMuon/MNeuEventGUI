from MuonDataLib.filters import PeakProperty

from MNeuEventGUI.amp.view import AmplitudeView
from MNeuEventGUI.plot_area.presenter import PlotAreaPresenter
from MNeuEventGUI.table.presenter import PresenterTemplate


class AmpPresenter(PresenterTemplate):
    """
    A class for the presenter of the Amplitude
    filter widget. This follows the MVP
    pattern.
    """
    def __init__(self):
        """
        This creates the presenter object for the
        widget.
        """

        # create a plot area
        self._plot = PlotAreaPresenter('amp')
        self._view = AmplitudeView(self)

    def load(self, data: PeakProperty):
        """
        Loads the amplitude data from
        a PeakProperty object.
        :param data: the PeakProperty object.
        :returns: the amplitude filter details
        """
        return data.Amplitudes

    def plot(self, data):
        """
        Creates a plot of the amplitude height and counts.
        :param data: the MuonData object, with an amlitude filter
        :returns: the graph object for histogram
        """
        hist, bins = data.get_peak_property_histogram('Amplitudes')
        return self._plot.plot(['Counts'],
                               [(bins[:-1] + bins[1:])/2.],
                               [hist],
                               'Amplitude')
