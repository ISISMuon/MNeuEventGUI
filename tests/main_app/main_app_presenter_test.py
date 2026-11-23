import os
import shutil
import sys
import tempfile
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
from data_paths import FILE, OTHER_FILE  # noqa: E402

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
# the tests use several batches
NUM_BATCHES = 3
EMPTY = [[]] * NUM_BATCHES


def per_batch(value):
    return [value] * NUM_BATCHES


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

        _ = MainAppPresenter(dummy_open, NUM_BATCHES)

        load.assert_called_once_with()
        control.assert_called_once_with(NUM_BATCHES)
        save.assert_called_once_with()

    def test_open_nxs(self):
        mock_open = mock.Mock(return_value='bob.nxs')
        app = MainAppPresenter(mock_open, NUM_BATCHES)
        new_name = app.open_nxs(1, 'old.nxs')

        self.assertEqual(new_name, 'bob.nxs')
        mock_open.assert_called_once_with(1)

    def test_open_nxs_no_update(self):
        mock_open = mock.Mock(return_value='bob.nxs')
        app = MainAppPresenter(mock_open, NUM_BATCHES)
        new_name = app.open_nxs(0, 'old.nxs')

        self.assertEqual(new_name, 'old.nxs')
        mock_open.assert_not_called()

    def test_confirm_load_with_time_filters(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        filters = {'Name_t': 'test',
                   'Start' + TT: 1,
                   'End' + TT: 3}
        state, clicks = app.confirm_load(2, [[], [filters], []], EMPTY, 1)
        self.assertTrue(state)
        self.assertEqual(clicks, 1)

    def test_confirm_load_with_log_filters(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        logs = [{'Name_log-table': 'mag_field'}]
        state, clicks = app.confirm_load(2, EMPTY, [[], [], logs], 1)
        self.assertTrue(state)
        self.assertEqual(clicks, 1)

    def test_confirm_load_no_filters(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        state, clicks = app.confirm_load(2, EMPTY, EMPTY, 1)
        self.assertFalse(state)
        self.assertEqual(clicks, 2)

    def change_settings(self, app):
        """
        Change the settings in the data, as the GUI
        would when the user edits them.
        :param app: the main app presenter
        """
        data = app.load.get_data
        data.set_time_type(1, 'exclude')
        data.set_amps_baseline(1, 2.7)
        data.set_histogram_settings(1, 0.5, 15.22, 1024)

    def assert_settings(self, result, expected, batch=None):
        """
        Check the settings reported by load_nxs.
        :param result: the values returned by load_nxs
        :param expected: the expected amplitude, time filter
        type and histogram settings
        :param batch: the batch to check (default is all of them)
        """
        batches = range(NUM_BATCHES) if batch is None else [batch]
        for k in batches:
            # the amplitude, time filter type and histogram settings
            self.assertEqual([values[k] for values in result[5:10]],
                             list(expected))

    def assert_headers(self, result):
        """
        Check there are column headers for every batch.
        :param result: the values returned by load_nxs
        """
        self.assertEqual(len(result[10]), NUM_BATCHES)
        for headers in result[10]:
            self.assertEqual(len(headers), 3)

    def test_load_nxs(self):

        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value=per_batch('amps'))
        result = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)
        self.assertEqual(result[0], 'plot')
        self.assertEqual(result[1], EMPTY)
        self.assertEqual(result[2], per_batch(False))
        self.assertEqual(result[3], EMPTY)
        self.assertEqual(result[4], per_batch(False))
        self.assert_settings(result, DEFAULT_SETTINGS)
        self.assert_headers(result)
        self.assertEqual(result[11], per_batch('amps'))
        self.assertEqual(result[12], per_batch(NO_EVENTS))

        self.assertMockOnce(app.plot, [])

    def test_load_nxs_keeps_settings_for_same_file(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value=per_batch('amps'))
        _ = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)

        self.change_settings(app)

        # the same file keeps the same data object
        result = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)
        self.assert_settings(result, [2.7, 'Exclude', 0.5, 15.22, 1024],
                             batch=1)
        # the other batches are unchanged
        self.assert_settings(result, DEFAULT_SETTINGS, batch=0)
        # the data has not changed, so neither has the number of events
        self.assertEqual(result[12], per_batch(no_update))

    def test_load_nxs_resets_settings_for_new_file(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value=per_batch('amps'))
        _ = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)

        self.change_settings(app)

        # a new file means a new data object, which uses its
        # own settings, so the GUI has to be updated to match
        result = app.load_nxs(OTHER_FILE, EMPTY, EMPTY, DEBUG)
        self.assert_settings(result, DEFAULT_SETTINGS)
        # the old number of events was for the old data
        self.assertEqual(result[12], per_batch(NO_EVENTS))

    def test_load_nxs_fails(self):

        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.gen_fake_data = mock.Mock(return_value=(np.array([1., 2., 3.]),
                                                    np.array([-1., 0., 1.])))
        bad_file = 'HIFI0.nxs'
        with pytest.raises(GUIError) as error:
            app.load_nxs(bad_file, EMPTY, EMPTY, DEBUG)

        self.assertEqual(str(error.value),
                         f'The file {bad_file} could not be loaded.')
        # the original error is kept, so the user can see it
        self.assertTrue(isinstance(error.value.__cause__, RuntimeError))

    def test_load_nxs_fails_keeps_the_loaded_file(self):
        """
        A file that fails to load is not the loaded file,
        so its name should not be left in the load bar.
        """
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)

        with pytest.raises(GUIError) as error:
            app.load_nxs('HIFI0.nxs', EMPTY, EMPTY, DEBUG)

        self.assertEqual(error.value.revert,
                         {'file_name': {'children': FILE}})
        self.assertEqual(app.load.file, FILE)

    def test_load_nxs_none(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.plot = mock.Mock(return_value='plot')
        app.gen_fake_data = mock.Mock(return_value=(np.array([1., 2., 3.]),
                                                    np.array([-1., 0., 1.])))
        bad_file = 'None'
        result = app.load_nxs(bad_file, EMPTY, EMPTY, DEBUG)
        self.assertEqual(result[0], 'plot')
        self.assertEqual(result[1], EMPTY)
        self.assertEqual(result[2], per_batch(True))
        self.assertEqual(result[3], EMPTY)
        self.assertEqual(result[4], per_batch(True))
        # there is no data to read the settings from
        self.assert_settings(result, [no_update]*5)
        self.assert_headers(result)
        self.assertEqual(result[11], per_batch({}))
        self.assertEqual(result[12], per_batch(NO_EVENTS))

        self.assertMockOnce(app.plot, [])

    def test_load_nxs_none_twice(self):
        """
        Cancelling the file browser leaves 'None' as the file,
        so a second cancel must not be treated as reloading it.
        """
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.plot = mock.Mock(return_value='plot')
        bad_file = 'None'
        _ = app.load_nxs(bad_file, EMPTY, EMPTY, DEBUG)

        result = app.load_nxs(bad_file, EMPTY, EMPTY, DEBUG)
        self.assertEqual(result[1], EMPTY)
        self.assertEqual(result[2], per_batch(True))
        self.assertEqual(result[3], EMPTY)
        self.assertEqual(result[4], per_batch(True))
        # there is still no data to read the settings from
        self.assert_settings(result, [no_update]*5)
        self.assertEqual(result[12], per_batch(NO_EVENTS))

    def test_load_nxs_fails_for_first_file(self):
        """
        The file name is an input of this callback, so putting it
        back after a failed load calls this method again. The first
        file to fail puts it back to there being no file, which has
        no data and so must not try to read any settings.
        """
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.plot = mock.Mock(return_value='plot')

        with pytest.raises(GUIError):
            app.load_nxs('HIFI0.nxs', EMPTY, EMPTY, DEBUG)

        # the name the pop up puts back into the load bar
        result = app.load_nxs(app.load.file, EMPTY, EMPTY, DEBUG)
        self.assertEqual(result[1], EMPTY)
        self.assertEqual(result[2], per_batch(True))
        self.assertEqual(result[3], EMPTY)
        self.assertEqual(result[4], per_batch(True))
        # the file never loaded, so there are no settings to read
        self.assert_settings(result, [no_update]*5)
        self.assertEqual(result[12], per_batch(NO_EVENTS))

    def test_load_nxs_with_filters(self):

        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        app.plot = mock.Mock(return_value='plot')
        app.plot_amps = mock.Mock(return_value=per_batch('amps'))
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

        result = app.load_nxs(FILE, per_batch(filters), per_batch(logs), DEBUG)
        # should clear the filters
        self.assertEqual(result[1], EMPTY)
        self.assertEqual(result[2], per_batch(False))
        self.assertEqual(result[3], EMPTY)
        self.assertEqual(result[4], per_batch(False))
        self.assert_settings(result, DEFAULT_SETTINGS)
        self.assert_headers(result)
        self.assertEqual(result[11], per_batch('amps'))
        self.assertEqual(result[12], per_batch(NO_EVENTS))

        self.assertMockOnce(app.plot, [])

    def test_load_nxs_with_filters_same_file(self):

        app = MainAppPresenter(dummy_open, NUM_BATCHES)

        result = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)
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
        result = app.load_nxs(FILE, per_batch(filters), per_batch(logs), DEBUG)
        self.assertEqual(result[0], plot)
        # should keep the filters
        self.assertEqual(result[1], per_batch(filters))
        self.assertEqual(result[2], per_batch(False))
        self.assertEqual(result[3], per_batch(logs))
        self.assertEqual(result[4], per_batch(False))
        self.assert_settings(result, DEFAULT_SETTINGS)
        self.assert_headers(result)
        self.assertEqual(result[11], amps)
        self.assertEqual(result[12], per_batch(no_update))

    def test_load_nxs_none_with_filters(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
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

        result = app.load_nxs(bad_file, per_batch(filters), per_batch(logs), DEBUG)
        self.assertEqual(result[0], 'plot')
        self.assertEqual(result[1], EMPTY)
        self.assertEqual(result[2], per_batch(True))
        self.assertEqual(result[3], EMPTY)
        self.assertEqual(result[4], per_batch(True))
        # there is no data to read the settings from
        self.assert_settings(result, [no_update]*5)
        self.assert_headers(result)
        self.assertEqual(result[11], per_batch({}))
        self.assertEqual(result[12], per_batch(NO_EVENTS))

        self.assertMockOnce(app.plot, [])

    def make_temp_dir(self):
        """
        :returns: a temporary directory, which is
        removed at the end of the test
        """
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        return directory

    def assert_saved_counts(self, directory, counts):
        """
        Check that a histogram file was saved for
        each batch, with the expected number of counts.
        :param directory: the directory the files were saved to
        :param counts: the expected counts for each batch
        """
        for k, count in enumerate(counts):
            file_name = os.path.join(directory, f'test_{k}.nxs')
            self.assertTrue(os.path.isfile(file_name))
            with h5py.File(file_name, 'r') as file:
                tmp = file['raw_data_1']['instrument']['detector_1']
                hist = tmp['counts']
                self.assertEqual(np.sum(hist), count)

    def save_nxs(self, app):
        """
        Save the histograms for all of the batches.
        :param app: the main app presenter
        :returns: the directory the files were saved to,
        """
        # todo: this is unnecessary once MneuEventLib PR #148 is merged
        app.load.get_data.calculate()

        directory = self.make_temp_dir()
        file_name = os.path.join(directory, 'test.nxs')
        name = app.save_data('n' + file_name, 0)
        self.assertEqual(name, file_name)
        return directory

    def test_save_nxs(self):
        """
        Just check that a file is saved
        for each batch, we assume its correct
        (covered by other unit tests).
        """
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        _ = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)

        directory = self.save_nxs(app)
        self.assert_saved_counts(directory, per_batch(64147))

    def test_save_nxs_with_filters(self):
        """
        Each batch is saved with its own filters.
        """
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        _ = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)

        data = app.load.get_data
        data.set_time_type(1, "exclude")
        data.add_time_filter(1, "unit", 1.2, 200)
        data.set_time_type(2, "include")
        data.add_time_filter(2, "unit", 1.2, 2)

        directory = self.save_nxs(app)
        self.assert_saved_counts(directory, [64147, 5755, 23745])

    def test_save_filters_active_batch(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        _ = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)

        data = app.load.get_data
        data.add_time_filter(2, "unit", 1.2, 2)

        file_name = os.path.join(self.make_temp_dir(), 'filters.json')
        name = app.save_data('j' + file_name, 2)
        self.assertEqual(name, file_name)

        # load into another batch to check the contents
        data.load_filters(0, file_name)
        self.assertEqual(list(data._dict(0)['time_filters']), ['unit'])

    def test_save_filters_after_removing_a_batch(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        _ = app.load_nxs(FILE, EMPTY, EMPTY, DEBUG)
        app.control.remove_batch(0, 2)

        # the batch with key 2 is now at index 1
        data = app.load.get_data
        data.add_time_filter(1, "unit", 1.2, 2)

        file_name = os.path.join(self.make_temp_dir(), 'filters.json')
        app.save_data('j' + file_name, 2)

        data.load_filters(0, file_name)
        self.assertEqual(list(data._dict(0)['time_filters']), ['unit'])

    def test_load_nxs_uses_current_batches(self):
        app = MainAppPresenter(dummy_open)
        app.control.add_batch()
        result = app.load_nxs(FILE, [[], []], [[], []], DEBUG)
        self.assertEqual(len(app.load.get_data), 2)
        self.assertEqual(len(result[1]), 2)

    def test_save_none(self):
        app = MainAppPresenter(dummy_open, NUM_BATCHES)
        result = app.save_data('None', 0)
        self.assertEqual(result, '')


if __name__ == '__main__':
    unittest.main()
