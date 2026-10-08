import os
import sys
import time

import h5py
import numpy as np

from MNeuEventGUI.main_app.view import MainApp
from MNeuEventGUI.test_helpers.gui import check_no_alert, wait_and_press_btn
from MNeuEventGUI.utils.errors import ERROR_PREFIX

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE, FILTER  # noqa: E402


def mock_load_nxs(n_clicks):
    return FILE


def mock_bad_load(n_clicks):
    return 'bad_file.txt'


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
    msg = dash_duo.find_element('#error_msg').text
    assert (msg.startswith(ERROR_PREFIX))
    assert ('bad_file.txt' in msg)

    # the full error is hidden until the user asks for it
    details = dash_duo.find_element('#error_details')
    assert (not details.is_displayed())

    dash_duo.find_element('#error_details_btn').click()
    time.sleep(.5)

    assert (details.is_displayed())
    assert ('Traceback' in details.text)


def test_load_nxs(dash_duo):
    app = MainApp(mock_load_nxs,
                  mock_load_json,
                  mock_save_nxs)
    dash_duo.start_server(app)
    dash_duo.wait_for_page()

    dash_duo.find_element('#Load').click()

    check_no_alert(dash_duo)
    assert (dash_duo.find_element('#file_name').text == FILE)

    wait_and_press_btn(dash_duo, 'Save')

    check_no_alert(dash_duo)
    with h5py.File(mock_save_nxs(0, 0)[1:], 'r') as file:
        tmp = file['raw_data_1']['instrument']['detector_1']
        hist = tmp['counts']
        assert (np.sum(hist) == 64147)
    os.remove(mock_save_nxs(0, 0)[1:])
