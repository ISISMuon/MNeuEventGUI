from MuonDataLib.GUI.presenter_template import PresenterTemplate
from MuonDataLib.GUI.load_bar.view import LoadBarView
from MuonDataLib.data.loader.load_events import load_events


class LoadBarPresenter(PresenterTemplate):
    """
    Class for the load bar's presenter.
    This follows the MVP pattern.
    The model is MuonDataLib.
    """
    def __init__(self):
        """
        Creates a load bar presenter
        """
        self._view = LoadBarView(self)
        self._data = None
        self.name = ''
        self._load_btn_press = 0
        self._load_filter_press = 0

    @property
    def file(self):
        """
        Gets the name of the current file
        :returns: the value for current file
        """
        return self.name

    def set_file(self, name):
        """
        A method to update the name
        of the current file
        """
        self.name = name

    def load_nxs(self, name):
        """
        Reads a muon event nexus file
        and creates a MuonDataLib object
        """
        self._data = load_events(name, 64)

    @property
    def get_data(self):
        """
        :returns: the loaded MuonDataLib
        object.
        """
        return self._data
