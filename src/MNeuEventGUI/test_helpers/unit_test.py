import numpy as np
import unittest


class TestHelper(unittest.TestCase):
    """
    A simple wrapper to make unit tests easier
    for nxs file
    """
    def compare_keys(self, nxs, expected):
        """
        Compares the options (keys) from a nexus file
        to an expected list
        :param nxs: the open nexus file (at the correct level)
        :param expected: the list of expected keys
        :return: the keys from the nexus file
        """
        keys = list(nxs.keys())
        # check same number of keys
        self.assertEqual(len(expected), len(keys))
        ref = expected
        # check keys match
        for value in keys:
            self.assertTrue(value in ref)
            ref.remove(value)
        # check all of the expected values have been seen
        self.assertEqual(len(ref), 0)
        return keys

    def assertString(self, group, key, expected):
        """
        The strings in nexus files are lists,
        with just one element. They also need
        decoding
        :param group: the open nexus group
        :param key: the key we want to check
        :param expected: the expected string
        """
        string_list = group[key]
        self.assertEqual(len(string_list), 1)
        self.assertEqual(string_list[0].decode(), expected)

    def assertArrays(self, array, ref):
        for j in range(len(array)):
            len_a = len(array)
            len_r = len(ref)
            msg = f'The arrays are not the same length: {len_a}, {len_r}'
            self.assertEqual(len_a, len_r, msg=msg)

            if isinstance(array[j], (list, np.ndarray)):
                self.assertArrays(array[j], ref[j])
            elif isinstance(array[j], str):
                self.assertEqual(array[j], ref[j])
            else:
                msg = f'values do not match in array {array[j]}, {ref[j]}'
                self.assertAlmostEqual(array[j], ref[j], 3, msg=msg)

    def assertMockOnce(self, mock, expected_args):
        """
        A method to check that a mock has the correct
        args. We assume that it is called once.
        This is needed as we often have arrays.
        :param mock: the mock object
        :param expected_args: the expected args for the
        call
        """
        mock.assert_called_once()
        args = mock.call_args[0]
        self.assertEqual(len(expected_args),
                         len(args))
        for k in range(len(args)):
            self.assertArrays(args[k],
                              expected_args[k])

    def check_shape(self, shape, k, x0, x1, y0, y1, ax):
        """
        A method to compare the vertical rectangles
        that have been added.
        :param shape: the details of the shape
        :param k: the domain index (starts at 0)
        :param x0: the start x value
        :param x1: the end x value
        :param y0: the start y value
        :param y1: the end y value
        """
        self.assertEqual(shape.fillcolor, 'PaleGreen')
        self.assertEqual(shape.layer, 'above')
        self.assertEqual(shape.line['color'], 'black')
        self.assertEqual(shape.line['width'], 4)
        self.assertEqual(shape.opacity, 0.3)
        self.assertEqual(shape.type, 'rect')
        self.assertEqual(shape.x0, x0)
        self.assertEqual(shape.x1, x1)
        self.assertEqual(shape.y0, y0)
        self.assertEqual(shape.y1, y1)
        self.assertEqual(shape['xref'], ax)

    def check_line(self, shape, k, *kwargs):
        self.assertEqual(shape['x0'], kwargs[0])
        self.assertEqual(shape['x1'], kwargs[1])
        self.assertEqual(shape['y0'], kwargs[2])
        self.assertEqual(shape['y1'], kwargs[3])

    def check_shapes(self, e_lines, e_rects):
        """
        Method to check the list of shapes currently applied
        to the plots.
        :param e_lines: the expected lines
        :param e_rects: the expected rectangles
        """
        N_plots = 2
        fig = self.get_fig
        shapes = fig.layout.shapes
        n = 0
        """
        The rectangles are out of order
        so we will manually just do the lines
        and then the rectangle
        """
        rects = []
        lines = []

        for k in range(len(shapes)):
            if shapes[k]['type'] == 'line':
                lines.append(shapes[k])
            else:
                rects.append(shapes[k])
        # factor 2 s we have 2 plots
        self.assertEqual(len(lines), N_plots*len(e_lines))
        for k in range(len(e_lines)):
            for j in range(N_plots):
                shape = lines[n]
                self.check_line(shape, j, *e_lines[k])
                n += 1

        self.assertEqual(len(rects), len(e_rects))
        for k in range(len(e_rects)):
            shape = rects[k]
            self.check_line(shape, k, *e_rects[k])

    @property
    def get_fig(self):
        """
        This is a method to allow different tests
        to use the above functions without needing
        to change or inject into them.
        This just gives the fig object.
        :returns: the fig object
        """
        raise NotImplementedError("Need to set a method to get the fig")
