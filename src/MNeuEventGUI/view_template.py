from MNeuEventGUI.utils.batch_callback import register

# the batch views that have had their callbacks registered
_REGISTERED_VIEWS = set()


class ViewTemplate:
    """
    A template for creating a view.
    This code uses the MVP pattern.
    """
    def __init__(self, presenter):
        """
        This creates the view object for the
        widget. The responses to the callbacks
        will be in the presenter.

        The callbacks for a batch's widget match every
        batch, so they are only registered for the first
        one. Later batches are registered so that the
        callbacks are passed on to them.
        """
        self._page = self.generate(presenter)
        if getattr(presenter, 'batch', None) is None:
            self.set_callbacks(presenter)
            return

        register(presenter)
        view_kind = (type(self), presenter.ID)
        if view_kind not in _REGISTERED_VIEWS:
            _REGISTERED_VIEWS.add(view_kind)
            self.set_callbacks(presenter)

    def generate(self, presenter):
        """
        This creates the view.
        However, in the template it raises
        an error to ensure it is implemented
        in all of the views.
        :returns: the widget layout
        """
        raise NotImplementedError("This view does not produce a widget")

    @property
    def layout(self):
        """
        :returns: the layout of the widget
        """
        return self._page

    def set_callbacks(self, presenter):
        """
        Sets the callbacks for the view.
        These are the responses to the
        view being interacted with.
        For a batch's widget, the callbacks should use
        presenter.callback_id for the IDs and
        utils.batch_callback.dispatch for the functions.
        :param presenter: the presenter,
        which will contain the appropriate
        responses to the callback.
        """
        return
