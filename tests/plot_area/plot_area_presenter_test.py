import unittest
from unittest import mock

import numpy as np

from MNeuEventGUI.plot_area.presenter import PlotAreaPresenter
from MNeuEventGUI.test_helpers.unit_test import TestHelper


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

    def test_component_id(self):
        self.assertEqual(self.presenter.component_id('_plot'),
                         'plot_test_plot')

    def assert_style(self, shape, colour, outline):
        self.assertEqual(shape.fillcolor, colour)
        self.assertEqual(shape.opacity, 0.3)
        if outline:
            self.assertEqual(shape.line['color'], 'black')
            self.assertEqual(shape.line['width'], 4)
        else:
            self.assertEqual(shape.line['width'], 0)

    def test_add_shaded_region_style(self):
        self.presenter.add_shaded_region(0.5, 0.8, 'red', False)
        for shape in self.presenter.fig.layout.shapes:
            self.assert_style(shape, 'red', False)

    def test_add_rect_style(self):
        self.presenter.add_rect(0.2, .3, .5, .6, axis=2,
                                colour='red', outline=False)
        shape = self.presenter.fig.layout.shapes[0]
        self.assert_style(shape, 'red', False)
        self.assertEqual(shape.yref, 'y2')

    def test_add_rect_domain(self):
        # full height of a single subplot
        self.presenter.add_rect(0.2, 0, 0.5, 1, '2', 'red', True,
                                domain=True)
        shapes = self.presenter.fig.layout.shapes
        self.assertEqual(len(shapes), 1)
        self.check_line(shapes[0], 0, 0.2, 0.5, 0, 1)
        self.assertEqual(shapes[0].xref, 'x2')
        self.assertEqual(shapes[0].yref, 'y2 domain')
        self.assert_style(shapes[0], 'red', True)

    def test_add_hline_row(self):
        self.presenter.add_hline(1.2, row=2, colour='red')
        shapes = self.presenter.fig.layout.shapes
        self.assertEqual(len(shapes), 1)
        self.assertEqual(shapes[0].yref, 'y2')
        self.assertEqual(shapes[0].line['color'], 'red')

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
        x_data = np.linspace(0, 4, 5)
        logs = [{'name': 'Temp', 'time': x_data, 'value': x_data*.1 - 2}]
        self.presenter.plot = mock.Mock()

        _ = self.presenter.new_plot(['Temp'], logs)
        self.assertMockOnce(self.presenter.plot,
                            [['Temp'],
                             [x_data],
                             [x_data*.1 - 2]])

    def test_new_plot_2(self):
        x_data = np.linspace(0, 4, 5)
        logs = [{'name': 'Temp', 'time': x_data, 'value': x_data*.1 - 2},
                {'name': 'I', 'time': x_data, 'value': x_data}]
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
