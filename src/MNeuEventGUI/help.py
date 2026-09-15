from MuonDataLib.help.help import help_app

from MNeuEventGUI.launch import launch_dash
from MNeuEventGUI.utils.main_window import BasicMainDashWindow


def launch_help():
    """
    A simple method to launch the help pages.
    """
    launch_dash(help_app, BasicMainDashWindow)
