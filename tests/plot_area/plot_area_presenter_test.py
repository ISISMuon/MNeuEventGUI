import unittest
from unittest import mock
from MuonDataLib.GUI.plot_area.presenter import PlotAreaPresenter
from MuonDataLib.test_helpers.unit_test import TestHelper
from MuonDataLib.test_helpers.utils import get_sample_logs
import numpy as np


class PlotAreaPresenterTest(TestHelper):

    def setUp(self):
        self.presenter = PlotAreaPresenter('plot_test')
        # just add a plot with 2 subplots
        self.presenter.plot(['test', 'data'],
                            [[0, 2], [0, 2]],
                            [[4, 5], [2, 4]])
        # clear the shapes
        self.presenter.fig.layout.shapes = []

    @property
    def get_fig(self):
        """
        Used in check shapes
        """
        return self.presenter.fig

    def test_ID(self):
        self.assertEqual(self.presenter.ID,
                         'plot_test')

    def test_shade_all(self):
        self.check_shapes([], [])

        self.presenter.shade_all()
        self.check_shapes([],
                          [[0, 2., 0, 1, 'x'],
                           [0, 2., 0, 1, 'x2'],
                           ])

    def test_add_shaded_region(self):
        self.check_shapes([], [])

        self.presenter.add_shaded_region(0.5, 0.8)
        self.check_shapes([],
                          [[0.5, 0.8, 0, 1, 'x'],
                           [0.5, 0.8, 0, 1, 'x2'],
                           ])

    def test_add_hline(self):
        self.check_shapes([], [])
        self.presenter.add_hline(1.2)
        self.check_shapes([[0, 1, 1.2, 1.2]],
                          [])

    def test_add_vline(self):
        self.check_shapes([], [])
        self.presenter.add_vline(1.2)
        self.check_shapes([[1.2, 1.2, 0, 1]],
                          [])

    def test_add_rect(self):
        self.check_shapes([], [])
        self.presenter.add_rect(0.2, .3, .5, .6, axis=1)
        self.check_shapes([],
                          [[0.2, 0.5, .3, .6, 'x1']])

    def test_reset_plot_range(self):
        self.assertEqual(self.presenter._min,
                         0.0)
        self.assertEqual(self.presenter._max,
                         2)

        self.presenter.reset_plot_range()
        self.assertEqual(self.presenter._min,
                         1000)
        self.assertEqual(self.presenter._max,
                         -1000)

    def test_new_plot_1(self):
        logs = get_sample_logs()

        x_data, _ = logs.get_sample_log('Temp').get_values()
        self.presenter.plot = mock.Mock()

        _ = self.presenter.new_plot(['Temp'], logs)
        self.assertMockOnce(self.presenter.plot,
                            [['Temp'],
                             [x_data],
                             [x_data*.1 - 2]])

    def test_new_plot_2(self):
        logs = get_sample_logs()
        x_data, _ = logs.get_sample_log('Temp').get_values()
        self.presenter.plot = mock.Mock()

        _ = self.presenter.new_plot(['Temp', 'I'], logs)
        self.assertMockOnce(self.presenter.plot,
                            [['Temp', 'I'],
                             [x_data, x_data],
                             [x_data*.1 - 2, x_data]])

    def assertAddTrace(self, expected_args, call):
        """
        A method to check that a mock has the correct
        args for add_trace. We assume that it is called once.
        This is needed as we have some arrays and multiple calls.
        :param expected_args: the expected args for the
        call
        :param call: the call number we are testing
        """
        args = self.presenter.add_trace.call_args_list[call][0]
        self.assertEqual(len(expected_args),
                         len(args))
        for k in range(len(args)):
            if k < 2:
                # only first 2 are arrays
                self.assertArrays(args[k],
                                  expected_args[k])
            else:
                self.assertEqual(args[k],
                                 expected_args[k])

    def test_plot(self):
        x_data = np.linspace(1, 2, 4)
        y_data = x_data * .5

        self.presenter.add_trace = mock.Mock()

        self.presenter.plot(['Temp'],
                            [x_data],
                            [y_data])

        self.assertEqual(self.presenter.add_trace.call_count, 1)
        self.assertAddTrace([x_data,
                             y_data,
                             'Temp',
                             1,
                             1],
                            0)

    def test_plot_3(self):
        x_data = np.linspace(1, 2, 4)
        y_data_1 = x_data * .5
        y_data_2 = x_data / 2.
        y_data_3 = x_data - 1

        self.presenter.add_trace = mock.Mock()

        self.presenter.plot(['Temp', 'B', 'I'],
                            [x_data, x_data, x_data],
                            [y_data_1, y_data_2, y_data_3])

        self.assertEqual(self.presenter.add_trace.call_count, 3)
        self.assertAddTrace([x_data,
                             y_data_1,
                             'Temp',
                             1,
                             1],
                            0)

        self.assertAddTrace([x_data,
                             y_data_2,
                             'B',
                             2,
                             1],
                            1)

        self.assertAddTrace([x_data,
                             y_data_3,
                             'I',
                             3,
                             1],
                            2)


if __name__ == '__main__':
    unittest.main()
