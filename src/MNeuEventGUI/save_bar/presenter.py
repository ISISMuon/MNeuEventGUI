from MNeuEventGUI.presenter_template import PresenterTemplate
from MNeuEventGUI.save_bar.view import SaveBarView


class SaveBarPresenter(PresenterTemplate):
    """
    A class for the save bar widget's presenter.
    This code follows the MVP pattern.
    """
    def __init__(self):
        """
        Creates the presenter
        """
        self._view = SaveBarView(self)
