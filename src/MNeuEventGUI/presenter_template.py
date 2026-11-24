from MNeuEventGUI.view_template import ViewTemplate


class PresenterTemplate:
    """
    This is a template class for a
    presenter. This code uses the
    MVP pattern.
    """
    # the prefix for the IDs of the widget's components
    ID = ''

    def __init__(self):
        """
        Creates a presenter with the
        view as a member
        """
        self._view = ViewTemplate(self)

    def component_id(self, suffix=''):
        """
        Gets the ID of a component of the widget.
        :param suffix: the suffix for the component
        :returns: the ID for the component
        """
        return self.ID + suffix

    @property
    def layout(self):
        """
        Gets the view of the widget
        :returns: the layout of the view
        """
        return self._view.layout
