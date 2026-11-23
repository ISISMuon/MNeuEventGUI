import unittest

from dash import ALL, MATCH, no_update

from MNeuEventGUI.utils.batch import (
    BATCH_COLOURS,
    INITIAL_BATCHES,
    active_batch_only,
    all_batches,
    batch_colour,
    batch_id,
    batch_label,
    matching_batch,
    per_batch,
)


class BatchUtilsTest(unittest.TestCase):

    def test_initial_batches(self):
        self.assertEqual(INITIAL_BATCHES, 1)

    def test_batch_id(self):
        self.assertEqual(batch_id('time-table', 2),
                         {'type': 'time-table', 'batch': 2})

    def test_all_batches(self):
        self.assertEqual(all_batches('time-table'),
                         {'type': 'time-table', 'batch': ALL})

    def test_matching_batch(self):
        self.assertEqual(matching_batch('time-table'),
                         {'type': 'time-table', 'batch': MATCH})

    def test_per_batch(self):
        self.assertEqual(per_batch(1, 4), [1] * 4)

    def test_active_batch_only(self):
        result = active_batch_only('filters.json', 1, 3)
        self.assertEqual(result, [no_update, 'filters.json', no_update])

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
