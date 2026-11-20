import sys
from pathlib import Path

from PySide6 import QtGui, QtWidgets

ICON_PATH = Path(__file__).parent / 'assets' / 'icon.png'


def launch_dash(dash_app, window):
    """
    A simple method to launch a dash app
    as part of a stand alone GUI.
    This works by placing the dash app
    inside of a pyqt web browser.
    """
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(str(ICON_PATH)))

    mainWin = window(dash_app)
    mainWin.show()

    sys.exit(app.exec())
