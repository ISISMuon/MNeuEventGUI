import os

from dash import ALL, MATCH, no_update
from plotly.colors import qualitative

# the number of batches (filter sets) the GUI starts with
INITIAL_BATCHES = 1

# the colours for the batches, these are reused if
# there are more batches than colours
BATCH_COLOURS = qualitative.Plotly


def batch_id(name, batch):
    """
    Gets a pattern matching ID for a component
    that is repeated for each batch.
    :param name: the name of the component
    :param batch: the key of the batch
    :returns: the ID for the component
    """
    return {'type': name, 'batch': batch}


def all_batches(name):
    """
    Gets a pattern matching ID that matches a
    component in every batch.
    :param name: the name of the component
    :returns: the ID for the components
    """
    return batch_id(name, ALL)


def matching_batch(name):
    """
    Gets a pattern matching ID that matches the
    component in the same batch as the rest of
    the callback.
    :param name: the name of the component
    :returns: the ID for the component
    """
    return batch_id(name, MATCH)


def per_batch(value, num_batches):
    """
    Repeats a value for every batch.
    :param value: the value for a single batch
    :param num_batches: the number of batches
    :returns: a list of the value for every batch
    """
    return [value] * num_batches


def batch_colour(batch):
    """
    Gets the colour for a batch. The colour only
    depends on the batch's index, so adding a batch
    does not change the colours of the others.
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


def active_batch_only(value, active, num_batches):
    """
    Gets the values to send to a component that is
    repeated for each batch, such that only the
    active batch is updated.
    :param value: the value for the active batch
    :param active: the index of the active batch
    :param num_batches: the number of batches
    :returns: the value for each batch
    """
    values = per_batch(no_update, num_batches)
    values[active] = value
    return values


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
