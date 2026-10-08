from dash import set_props

ERROR_PREFIX = 'An error occurred: '


class GUIError(Exception):
    """
    An error that also needs to put the GUI back
    into a sensible state.

    A callback that raises does not update its own
    outputs, so anything that still has to be set
    (e.g. reverting an invalid table edit) is carried
    on the exception and applied by display_error.
    """
    def __init__(self, msg, revert=None):
        """
        :param msg: the message to show the user
        :param revert: a dict of component ID to a dict
        of the props to set on that component
        """
        super().__init__(msg)
        self.revert = revert or {}


def display_error(err):
    """
    The global callback error handler. Instead of the
    exception only reaching the terminal, it is shown
    in the alert at the top of the GUI.
    :param err: the exception raised by the callback
    """
    if isinstance(err, GUIError):
        for component_id, props in err.revert.items():
            set_props(component_id, props)

    set_props('error_msg', {'children': ERROR_PREFIX + str(err)})
    set_props('error', {'is_open': True})
