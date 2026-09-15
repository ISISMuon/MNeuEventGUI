from MuonDataLib.GUI.main_app.view import MainApp
from MuonDataLib.GUI.load_bar.view import CURRENT
from MuonDataLib.test_helpers.GUI import (check_no_alert,
                                          wait_and_press_btn)

import os
import h5py
import numpy as np
import sys
import time

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE, FILTER  # noqa: E402


def mock_load_nxs(n_clicks):
    return CURRENT + FILE


def mock_bad_load(n_clicks):
    return CURRENT + 'bad_file.txt'


def mock_load_json(n_clicks):
    return FILTER


def mock_save_nxs(n_nxs, n_json):
    return 'n' + 'test.nxs'


def test_launch(dash_duo):
    """
    For some reason the first test
    does not load correctly.
    So we add this dummy to
    avoid fake failures.
    """
    app = MainApp(mock_load_nxs,
                  mock_load_json,
                  mock_save_nxs)
    dash_duo.start_server(app)
    dash_duo.wait_for_page()

    pass


def test_load_nxs_error(dash_duo):

    app = MainApp(mock_bad_load,
                  mock_load_json,
                  mock_save_nxs)
    dash_duo.start_server(app)
    dash_duo.wait_for_page()

    dash_duo.find_element('#Load').click()

    time.sleep(.1)
    # check that the error alert has appeared with correct msg
    assert (dash_duo.find_element('#error').is_enabled)
    msg = "An error occurred: The file bad_file.txt cannot be read"
    assert (dash_duo.find_element('#error_msg').text == msg)


def test_load_nxs(dash_duo):
    app = MainApp(mock_load_nxs,
                  mock_load_json,
                  mock_save_nxs)
    dash_duo.start_server(app)
    dash_duo.wait_for_page()

    dash_duo.find_element('#Load').click()

    check_no_alert(dash_duo)
    assert (dash_duo.find_element('#file_name').text == CURRENT + FILE)

    wait_and_press_btn(dash_duo, 'Save')

    check_no_alert(dash_duo)
    with h5py.File(mock_save_nxs(0, 0)[1:], 'r') as file:
        tmp = file['raw_data_1']['instrument']['detector_1']
        hist = tmp['counts']
        assert (np.sum(hist) == 64147)
    os.remove(mock_save_nxs(0, 0)[1:])
