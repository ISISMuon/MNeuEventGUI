from dash import ALL, no_update
from plotly.colors import sample_colorscale

# the number of batches (filter sets) the GUI provides
NUM_BATCHES = 3


def batch_id(name, batch):
    """
    Gets a pattern matching ID for a component
    that is repeated for each batch.
    :param name: the name of the component
    :param batch: the index of the batch
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


def per_batch(value):
    """
    Repeats a value for every batch.
    :param value: the value for a single batch
    :returns: a list of the value for every batch
    """
    return [value] * NUM_BATCHES


def batch_colour(batch, num_batches=NUM_BATCHES):
    """
    Gets the colour for a batch. The colours are
    sampled from the middle of equal width sections
    of Viridis, to avoid the hard to see ends.
    :param batch: the index of the batch
    :param num_batches: the total number of batches
    :returns: the colour as an rgb string
    """
    return sample_colorscale('Viridis',
                             [(batch + 0.5) / num_batches])[0]


def tab_id(batch):
    """
    Gets the ID of the tab for a batch.
    :param batch: the index of the batch
    :returns: the tab ID
    """
    return str(batch)


def active_batch(active_tab):
    """
    Gets the index of the batch for the active tab.
    :param active_tab: the ID of the active tab
    :returns: the index of the batch
    """
    if active_tab is None:
        return 0
    return int(active_tab)


def active_batch_only(value, active_tab):
    """
    Gets the values to send to a component that is
    repeated for each batch, such that only the
    active batch is updated.
    :param value: the value for the active batch
    :param active_tab: the ID of the active batch tab
    :returns: the value for each batch
    """
    values = per_batch(no_update)
    values[active_batch(active_tab)] = value
    return values
