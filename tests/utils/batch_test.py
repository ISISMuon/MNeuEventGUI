import unittest

from MNeuEventGUI.utils.batch import (
    BATCH_COLOURS,
    INITIAL_BATCHES,
    batch_colour,
    batch_file_names,
    batch_label,
)


class BatchUtilsTest(unittest.TestCase):

    def test_batch_file_names(self):
        self.assertEqual(batch_file_names('/a/out.nxs', 2),
                         ['/a/out_0.nxs', '/a/out_1.nxs'])

    def test_initial_batches(self):
        self.assertEqual(INITIAL_BATCHES, 1)

    def test_batch_label(self):
        self.assertEqual(batch_label(2), 'Batch 2')

    def test_batch_colours_unique(self):
        colours = [batch_colour(k) for k in range(len(BATCH_COLOURS))]
        self.assertEqual(len(set(colours)), len(BATCH_COLOURS))

    def test_batch_colours_reused(self):
        # there can be more batches than colours
        self.assertEqual(batch_colour(len(BATCH_COLOURS)), batch_colour(0))


if __name__ == '__main__':
    unittest.main()
