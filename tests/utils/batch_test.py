import unittest

from plotly.colors import sample_colorscale

from MNeuEventGUI.utils.batch import (
    NUM_BATCHES,
    active_batch,
    batch_colour,
    batch_id,
    tab_id,
)


class BatchUtilsTest(unittest.TestCase):

    def test_num_batches(self):
        self.assertEqual(NUM_BATCHES, 3)

    def test_batch_id(self):
        self.assertEqual(batch_id('time-table', 2),
                         {'type': 'time-table', 'batch': 2})

    def test_batch_colour(self):
        # colours are sampled from the middle of
        # equal width sections of Viridis
        expect = sample_colorscale('Viridis', [1/6, 1/2, 5/6])
        for k in range(3):
            self.assertEqual(batch_colour(k, 3), expect[k])

    def test_batch_colour_default_num_batches(self):
        self.assertEqual(batch_colour(0),
                         batch_colour(0, NUM_BATCHES))

    def test_batch_colours_unique(self):
        colours = [batch_colour(k) for k in range(NUM_BATCHES)]
        self.assertEqual(len(set(colours)), NUM_BATCHES)

    def test_tab_id_round_trip(self):
        for k in range(NUM_BATCHES):
            self.assertEqual(active_batch(tab_id(k)), k)

    def test_active_batch_none(self):
        # before a tab is selected, the first batch is active
        self.assertEqual(active_batch(None), 0)


if __name__ == '__main__':
    unittest.main()
