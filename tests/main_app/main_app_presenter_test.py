import os
import sys
import unittest
from unittest import mock

import h5py
import numpy as np
import pytest
from dash import no_update

from MNeuEventGUI.main_app.presenter import MainAppPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper
from MNeuEventGUI.utils.errors import GUIError

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from data_paths import FILE, FILTER, OTHER_FILE  # noqa: E402

"""
Only testing debug = False,
as it will removed in the long term
"""
DEBUG = False
TT = '_time-table'
# the amplitude, time filter type and histogram settings
# that a freshly loaded data object reports
DEFAULT_SETTINGS = [0, 'Include', 0., 32.768, 2048]
# the number of events is only known after Calculate is pressed
NO_EVENTS = 'Number of events: Not Calculated'
DUMMY_SETTINGS = ([], 0, 0, 32.768, 2048, DEBUG)

def dummy_open(N_clicks):
    return 'bob.nxs'

def osc(x, A, omega, phi):
    return A*np.sin(omega*x + phi)

def make_noise(vec, RNG):
    """
    A simple function for creating Gassian noise
    with the same shape as the input.
    :param vec: the data to add noise to
    :param RNG: the random number generator
    :return: the noise to be added
    """
    return RNG.normal(0, 0.1, vec.shape)

def create_data_from_function(x1, x2, dx, params, function, seed=None):
    """
    A method for creating mock data that is roughly given by
    the function and parameters.
    This method will add some random noise to both the x and
    y values.
    :param x1: the start x value
    :param x2: the end x value
    :param dx: the average step size for x
    :param params: a list of the parameters for the function
    :param function: a callable of the function to use
    (must return the y values)
    :param seed: the seed for the random number generator (optional)
    :return: The x and y values with noise.
    """
    x = np.arange(x1, x2, dx)
    RNG = np.random.default_rng(seed=seed)
    noise = make_noise(x, RNG)*dx
    x += noise
    y = function(x, *params)
    y_noise = make_noise(y, RNG)
    y = y*(1 + 0.1*y_noise/np.max(y_noise))
    return x, y

def gen_fake_data(data):
        """
        This creates fake data for the sample log.
        It will not be present long term.
        We assume one data point per second.
        :param data: the muon event data object
        :returns: the fake data
        """
        frame_start_times = data.get_frame_start_times()
        start = frame_start_times[0]
        end = frame_start_times[-1] + 1
        # 1 days worth of logs at 1 per second
        N = 60*60*24
        step = (end - start)/N
        return create_data_from_function(start, end,
                                         step,
                                         [3, 6.1, 0.91],
                                         osc, seed=1)

class MainAppPresenterTest(TestHelper):

    @mock.patch("MNeuEventGUI.main_app.presenter.LoadBarPresenter")
    @mock.patch("MNeuEventGUI.main_app.presenter.ControlPanePresenter")
    @mock.patch("MNeuEventGUI.main_app.presenter.SaveBarPresenter")
    def test_init(self, save, control, load):

        load.return_value = mock.Mock()
        control.return_value = mock.Mock()
        save.return_value = mock.Mock()

        _ = MainAppPresenter(dummy_open)

        load.assert_called_once_with()
        control.assert_called_once_with()
        save.assert_called_once_with()

    def test_open_nxs(self):
        mock_open = mock.Mock(return_value='bob.nxs')
        app = MainAppPresenter(mock_open)
        new_name = app.open_nxs(1, 'old.nxs')

        self.assertEqual(new_name, 'bob.nxs')
        mock_open.assert_called_once_with(1)

    def test_open_nxs_no_update(self):
        mock_open = mock.Mock(return_value='bob.nxs')
        app = MainAppPresenter(mock_open)
        new_name = app.open_nxs(0, 'old.nxs')

        self.assertEqual(new_name, 'old.nxs')
        mock_open.assert_not_called()

    def test_confirm_load_with_filters(self):
        app = MainAppPresenter(dummy_open)
        filters = {'Name_t': 'test',
                   'Start' + TT: 1,
                   'End' + TT: 3}
        state, clicks = app.confirm_load(2, filters, 1)
        self.assertTrue(state)
        self.assertEqual(clicks, 1)

    def test_confirm_load_no_filters(self):
        app = MainAppPresenter(dummy_open)
        state, clicks = app.confirm_load(2, {}, 1)
        self.assertFalse(state)
        self.assertEqual(clicks, 2)

    def change_settings(self, app):
        """
        Change the settings in the data, as the GUI
        would when the user edits them.
        :param app: the main app presenter
        """
        data = app.load.get_data
        data.set_time_type(0, 'exclude')
        data.set_amps_baseline(0, 2.7)
        data.set_histogram_settings(0, 0.5, 15.22, 1024)

    def assert_settings(self, result, expected):
        """
        Check the settings reported by load_nxs.
        :param result: the values returned by load_nxs
        :param expected: the expected amplitude, time filter
        type and histogram settings
        """
        # the amplitude, time filter type and histogram settings
        self.assertEqual(list(result[5:10]), list(expected))

    def test_load_nxs(self):

        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value='amps')
        result = app.load_nxs(FILE, [], [], DEBUG)
        self.assertEqual(result[0], 'plot')
        self.assertEqual(result[1], [])
        self.assertEqual(result[2], False)
        self.assertEqual(result[3], [])
        self.assertEqual(result[4], False)
        self.assert_settings(result, DEFAULT_SETTINGS)
        self.assertEqual(len(result[10]), 3)
        self.assertEqual(result[11], 'amps')
        self.assertEqual(result[12], NO_EVENTS)

        self.assertMockOnce(app.plot, [])

    def test_load_nxs_keeps_settings_for_same_file(self):
        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value='amps')
        _ = app.load_nxs(FILE, [], [], DEBUG)

        self.change_settings(app)

        # the same file keeps the same data object
        result = app.load_nxs(FILE, [], [], DEBUG)
        self.assert_settings(result, [2.7, 'Exclude', 0.5, 15.22, 1024])
        # the data has not changed, so neither has the number of events
        self.assertEqual(result[12], no_update)

    def test_load_nxs_resets_settings_for_new_file(self):
        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value='amps')
        _ = app.load_nxs(FILE, [], [], DEBUG)

        self.change_settings(app)

        # a new file means a new data object, which uses its
        # own settings, so the GUI has to be updated to match
        result = app.load_nxs(OTHER_FILE, [], [], DEBUG)
        self.assert_settings(result, DEFAULT_SETTINGS)
        # the old number of events was for the old data
        self.assertEqual(result[12], NO_EVENTS)

    def test_load_nxs_fails(self):

        app = MainAppPresenter(dummy_open)
        app.gen_fake_data = mock.Mock(return_value=(np.array([1., 2., 3.]),
                                                    np.array([-1., 0., 1.])))
        bad_file = 'HIFI0.nxs'
        with pytest.raises(GUIError) as error:
            app.load_nxs(bad_file, [], [], DEBUG)

        self.assertEqual(str(error.value),
                         f'The file {bad_file} could not be loaded.')
        # the original error is kept, so the user can see it
        self.assertTrue(isinstance(error.value.__cause__, RuntimeError))

    def test_load_nxs_fails_keeps_the_loaded_file(self):
        """
        A file that fails to load is not the loaded file,
        so its name should not be left in the load bar.
        """
        app = MainAppPresenter(dummy_open)
        app.load_nxs(FILE, [], [], DEBUG)

        with pytest.raises(GUIError) as error:
            app.load_nxs('HIFI0.nxs', [], [], DEBUG)

        self.assertEqual(error.value.revert,
                         {'file_name': {'children': FILE}})
        self.assertEqual(app.load.file, FILE)

    def test_load_nxs_none(self):
        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')
        app.gen_fake_data = mock.Mock(return_value=(np.array([1., 2., 3.]),
                                                    np.array([-1., 0., 1.])))
        bad_file = 'None'
        result = app.load_nxs(bad_file, [], [], DEBUG)
        self.assertEqual(result[0], 'plot')
        self.assertEqual(result[1], [])
        self.assertEqual(result[2], True)
        self.assertEqual(result[3], [])
        self.assertEqual(result[4], True)
        # there is no data to read the settings from
        self.assert_settings(result, [no_update]*5)
        self.assertEqual(len(result[10]), 3)
        self.assertEqual(result[11], {})
        self.assertEqual(result[12], NO_EVENTS)

        self.assertMockOnce(app.plot, [])

    def test_load_nxs_none_twice(self):
        """
        Cancelling the file browser leaves 'None' as the file,
        so a second cancel must not be treated as reloading it.
        """
        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')
        bad_file = 'None'
        _ = app.load_nxs(bad_file, [], [], DEBUG)

        result = app.load_nxs(bad_file, [], [], DEBUG)
        self.assertEqual(result[1], [])
        self.assertEqual(result[2], True)
        self.assertEqual(result[3], [])
        self.assertEqual(result[4], True)
        # there is still no data to read the settings from
        self.assert_settings(result, [no_update]*5)
        self.assertEqual(result[12], NO_EVENTS)

    def test_load_nxs_fails_for_first_file(self):
        """
        The file name is an input of this callback, so putting it
        back after a failed load calls this method again. The first
        file to fail puts it back to there being no file, which has
        no data and so must not try to read any settings.
        """
        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')

        with pytest.raises(GUIError):
            app.load_nxs('HIFI0.nxs', [], [], DEBUG)

        # the name the pop up puts back into the load bar
        result = app.load_nxs(app.load.file, [], [], DEBUG)
        self.assertEqual(result[1], [])
        self.assertEqual(result[2], True)
        self.assertEqual(result[3], [])
        self.assertEqual(result[4], True)
        # the file never loaded, so there are no settings to read
        self.assert_settings(result, [no_update]*5)
        self.assertEqual(result[12], NO_EVENTS)

    def test_load_nxs_with_filters(self):

        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value='amps')
        filters = [{'Name' + TT: 'test', 'Start' + TT: 0, 'End' + TT: 1}]
        logs = [{'Delete_log-table': '',
                 'Name_log-table': 'mag_field',
                 'sample_log-table': 'B',
                 'filter_log-table': 'between',
                 'magic': 'between',
                 'y0_log-table': 0,
                 'yN_log-table': 1,
                 'y_min_log-table': 0,
                 'y_max_log-table': 3}]

        result = app.load_nxs(FILE, filters, logs, DEBUG)
        # should clear the filters
        self.assertEqual(result[1], [])
        self.assertEqual(result[2], False)
        self.assertEqual(result[3], [])
        self.assertEqual(result[4], False)
        self.assert_settings(result, DEFAULT_SETTINGS)
        self.assertEqual(len(result[10]), 3)
        self.assertEqual(result[11], 'amps')
        self.assertEqual(result[12], NO_EVENTS)

        self.assertMockOnce(app.plot, [])

    def test_load_nxs_with_filters_same_file(self):

        app = MainAppPresenter(dummy_open)

        result = app.load_nxs(FILE, [], [], DEBUG)
        plot = result[0]
        amps = result[11]

        # add some filters after load
        filters = [{'Name' + TT: 'test', 'Start' + TT: 0, 'End' + TT: 1}]
        logs = [{'Delete_log-table': '',
                 'Name_log-table': 'mag_field',
                 'sample_log-table': 'B',
                 'filter_log-table': 'between',
                 'magic': 'between',
                 'y0_log-table': 0,
                 'yN_log-table': 1,
                 'y_min_log-table': 0,
                 'y_max_log-table': 3}]
        # load the same data again
        result = app.load_nxs(FILE, filters, logs, DEBUG)
        self.assertEqual(result[0], plot)
        # should keep the filters
        self.assertEqual(result[1], filters)
        self.assertEqual(result[2], False)
        self.assertEqual(result[3], logs)
        self.assertEqual(result[4], False)
        self.assert_settings(result, DEFAULT_SETTINGS)
        self.assertEqual(len(result[10]), 3)
        self.assertEqual(result[11], amps)
        self.assertEqual(result[12], no_update)

    def test_load_nxs_none_with_filters(self):
        app = MainAppPresenter(dummy_open)
        app.plot = mock.Mock(return_value='plot')
        app.gen_fake_data = mock.Mock(return_value=(np.array([1., 2., 3.]),
                                                    np.array([-1., 0., 1.])))
        bad_file = 'None'
        filters = [{'Name': 'test', 'Start': 0, 'End': 1}]
        logs = [{'Delete_log-table': '',
                 'Name_log-table': 'mag_field',
                 'sample_log-table': 'B',
                 'filter_log-table': 'between',
                 'magic': 'between',
                 'y0_log-table': 0,
                 'yN_log-table': 1,
                 'y_min_log-table': 0,
                 'y_max_log-table': 3}]

        result = app.load_nxs(bad_file, filters, logs, DEBUG)
        self.assertEqual(result[0], 'plot')
        self.assertEqual(result[1], [])
        self.assertEqual(result[2], True)
        self.assertEqual(result[3], [])
        self.assertEqual(result[4], True)
        # there is no data to read the settings from
        self.assert_settings(result, [no_update]*5)
        self.assertEqual(len(result[10]), 3)
        self.assertEqual(result[11], {})
        self.assertEqual(result[12], NO_EVENTS)

        self.assertMockOnce(app.plot, [])

    def test_load_filter(self):
        app = MainAppPresenter(dummy_open)
        _ = app.load_nxs(FILE, [], [], DEBUG)
        result = app.load_filter(FILTER)
        self.assertCountEqual(result[0], [{'Name' + TT: 'first',
                                      'Start' + TT: 0.01,
                                      'End' + TT: 0.02},
                                     {'Name' + TT: 'second',
                                      'Start' + TT: 0.05,
                                      'End' + TT: 0.06},
                                     ])
        self.assertCountEqual(result[1], [{'Name_log-table': 'log_default_1',
                                      'filter_log-table': 'between',
                                      'magic': 'between',
                                      'sample_log-table': 'Temp',
                                      'y0_log-table': 0.0044,
                                      'yN_log-table': 0.163,
                                      'y_max_log-table': np.float64(39.0),
                                      'y_min_log-table': np.float64(35.0)
                                      }])

        self.assertEqual(result[2], 3.14)
        self.assertEqual(result[3], 'Include')
        # the filter file does not store the histogram settings
        self.assertEqual(result[4], 0.)
        self.assertEqual(result[5], 32.768)
        self.assertEqual(result[6], 2048)
        self.assertEqual(len(result[7]), 3)

    def test_load_filter_fail(self):
        bad_file = 'nonexistent_filters.json'

        app = MainAppPresenter(dummy_open)
        _ = app.load_nxs(FILE, [], [], DEBUG)

        with pytest.raises(GUIError) as error:
            app.load_filter(bad_file)

        self.assertEqual(str(error.value),
                         f'The filter file {bad_file} could not be loaded.')
        # the original error is kept, so the user can see it
        self.assertTrue(isinstance(error.value.__cause__, RuntimeError))

    def test_save_nxs(self):
        """
        Just check that a file is saved
        we assume its correct (covered
        by other unit tests).
        """
        app = MainAppPresenter(dummy_open)
        _ = app.load_nxs(FILE, [], [], DEBUG)

        # todo: this is unnecessary once MneuEventLib PR #148 is merged
        data = app.load.get_data
        data.calculate()

        dtype = 'n'
        file_name = 'test.nxs'
        name = app.save_data(dtype + file_name)
        self.assertTrue(os.path.isfile(file_name))

        with h5py.File(file_name, 'r') as file:
            tmp = file['raw_data_1']['instrument']['detector_1']
            hist = tmp['counts']
            self.assertEqual(np.sum(hist), 64147)

        os.remove(file_name)
        self.assertEqual(name, file_name)

    def test_save_nxs_with_exclude_filter(self):
        """
        Just check that a file is saved
        we assume its correct (covered
        by other unit tests).
        """
        app = MainAppPresenter(dummy_open)
        _ = app.load_nxs(FILE, [], [], DEBUG)

        # todo: this is unnecessary once MneuEventLib PR #148 is merged
        data = app.load.get_data
        data.set_time_type(0, "exclude")
        data.add_time_filter(0, "unit", 1.2, 200)
        data.calculate()

        dtype = 'n'
        file_name = 'test.nxs'
        name = app.save_data(dtype + file_name)
        self.assertTrue(os.path.isfile(file_name))

        with h5py.File(file_name, 'r') as file:
            tmp = file['raw_data_1']['instrument']['detector_1']
            hist = tmp['counts']
            self.assertEqual(np.sum(hist), 5755)

        os.remove(file_name)
        self.assertEqual(name, file_name)

    def test_save_nxs_with_include_filter(self):
        """
        Just check that a file is saved
        we assume its correct (covered
        by other unit tests).
        """
        app = MainAppPresenter(dummy_open)
        _ = app.load_nxs(FILE, [], [], DEBUG)

        # todo: this is unnecessary once MneuEventLib PR #148 is merged
        data = app.load.get_data
        data.set_time_type(0, "include")
        data.add_time_filter(0, "unit", 1.2, 2)
        data.calculate()

        dtype = 'n'
        file_name = 'test.nxs'

        name = app.save_data(dtype + file_name)
        self.assertTrue(os.path.isfile(file_name))

        with h5py.File(file_name, 'r') as file:
            tmp = file['raw_data_1']['instrument']['detector_1']
            hist = tmp['counts']
            self.assertEqual(np.sum(hist), 23745)

        os.remove(file_name)
        self.assertEqual(name, file_name)

    def test_save_none(self):
        app = MainAppPresenter(dummy_open)
        result = app.save_data('None')
        self.assertEqual(result, '')


if __name__ == '__main__':
    unittest.main()
