from MNeuEventGUI.utils.batch import batch_id
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
    # (None if shared by all batches)
    batch = None

    def __init__(self):
        """
        Creates a presenter with the
        view as a member
        """
        self._view = ViewTemplate(self)

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
        return batch_id(name, self.batch)

    @property
    def layout(self):
        """
        Gets the view of the widget
        :returns: the layout of the view
        """
        return self._view.layout
