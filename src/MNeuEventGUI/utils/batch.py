"""
Batches (filter sets) share one set of filter widgets. The widgets
show the active batch, which is the value of the ACTIVE dropdown
(the index of the batch in the data). Callbacks that change a batch
take State(ACTIVE, 'value') to know which batch to change. When the
active batch changes, or a batch is added or removed (which changes
NUM_BATCHES), the widgets are refilled from the data.
"""
import os

from plotly.colors import qualitative

# the ID of the dropdown for choosing the active batch.
# Its value is the index of the active batch.
ACTIVE = 'batch-select'
# the ID of the store for the number of batches
NUM_BATCHES = 'batch-count'

# the number of batches (filter sets) the GUI starts with
INITIAL_BATCHES = 1

# the colours for the batches, these are reused if
# there are more batches than colours
BATCH_COLOURS = qualitative.Plotly


def batch_colour(batch):
    """
    Gets the colour for a batch.
    :param batch: the index of the batch
    :returns: the colour
    """
    return BATCH_COLOURS[batch % len(BATCH_COLOURS)]


def batch_label(batch):
    """
    Gets the label for a batch.
    :param batch: the index of the batch
    :returns: the label
    """
    return f'Batch {batch}'


def batch_file_names(file, num_batches):
    """
    Gets the names of the files that are saved for
    each batch, which have the batch index added
    before the extension (e.g. out.nxs becomes
    out_0.nxs, out_1.nxs, ...).
    :param file: the name of the file to save to
    :param num_batches: the number of batches
    :returns: the name of the file for each batch
    """
    stem, ext = os.path.splitext(file)
    return [f'{stem}_{index}{ext}' for index in range(num_batches)]
