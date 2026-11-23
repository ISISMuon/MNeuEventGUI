from MNeuEventGUI.utils.batch import batch_id, matching_batch
from MNeuEventGUI.view_template import ViewTemplate


class PresenterTemplate:
    """
    This is a template class for a
    presenter. This code uses the
    MVP pattern.
    """
    # the prefix for the IDs of the widget's components
    ID = ''
    # the index of the batch the widget is for
    # (None if shared by all batches). This is the
    # index of the batch in the data, so it changes
    # if an earlier batch is removed.
    batch = None
    # the key used in the IDs of the batch's components.
    # Unlike the index, this does not change, so the
    # components of the other batches are untouched when
    # a batch is removed. None means it is the index.
    _key = None

    def __init__(self):
        """
        Creates a presenter with the
        view as a member
        """
        self._view = ViewTemplate(self)

    @property
    def key(self):
        """
        :returns: the key used in the IDs of the
        batch's components (None if shared by all batches)
        """
        return self.batch if self._key is None else self._key

    def set_index(self, index):
        """
        Sets the index of the batch in the data,
        without changing the IDs of its components.
        :param index: the new index of the batch
        """
        self._key = self.key
        self.batch = index

    def component_id(self, suffix=''):
        """
        Gets the ID of a component of the widget.
        If the widget is for a batch, the ID is
        unique to the batch.
        :param suffix: the suffix for the component
        :returns: the ID for the component
        """
        name = self.ID + suffix
        if self.batch is None:
            return name
        return batch_id(name, self.key)

    def callback_id(self, suffix=''):
        """
        Gets the ID of a component of the widget for
        use in a callback. If the widget is for a batch,
        this matches the component in whichever batch
        triggered the callback (see utils/batch_callback.py).
        :param suffix: the suffix for the component
        :returns: the ID for the callback
        """
        name = self.ID + suffix
        if self.batch is None:
            return name
        return matching_batch(name)

    @property
    def layout(self):
        """
        Gets the view of the widget
        :returns: the layout of the view
        """
        return self._view.layout
