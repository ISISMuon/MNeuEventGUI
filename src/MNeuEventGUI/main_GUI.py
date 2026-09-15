from MNeuEventGUI.main_app.view import MainApp
from MNeuEventGUI.utils.main_window import MainDashWindow
from MNeuEventGUI.launch import launch_dash


def launch_GUI():
    """
    A simple method to launch the filtering GUI.
    """
    launch_dash(MainApp, MainDashWindow)
