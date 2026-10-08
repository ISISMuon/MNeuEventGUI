import traceback

import dash_bootstrap_components as dbc
from dash import html, set_props

ERROR_PREFIX = 'An error occurred: '
UNEXPECTED_MSG = 'Something went wrong.'
SHOW_DETAILS = 'Show details'
HIDE_DETAILS = 'Hide details'

ALERT = 'error'
MSG = 'error_msg'
DETAILS = 'error_details'
DETAILS_BTN = 'error_details_btn'
DETAILS_COLLAPSE = 'error_details_collapse'


class GUIError(Exception):
    """
    An error with a message for the user, which may
    also need to put the GUI back into a sensible state.

    The message should say what went wrong in terms the
    user understands (e.g. "The file could not be loaded").
    The error that caused it should be kept by raising with
    `from`, so the user can still see the full original
    error in the details dropdown of the alert.

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


def error_alert():
    """
    Creates the alert used to report errors. It shows a
    readable message, with the full original error hidden
    behind a dropdown (see display_error).
    :returns: the alert component
    """
    return dbc.Alert([html.H4("   ERROR MESSAGE",
                              className='bi-x-octagon-fill'),
                      html.P("Error", id=MSG),
                      dbc.Button(SHOW_DETAILS,
                                 id=DETAILS_BTN,
                                 color='danger',
                                 size='sm',
                                 n_clicks=0),
                      dbc.Collapse(html.Pre('',
                                            id=DETAILS,
                                            className='mt-2 mb-0'),
                                   id=DETAILS_COLLAPSE,
                                   is_open=False)],
                     id=ALERT,
                     dismissable=True,
                     fade=False,
                     color='danger',
                     is_open=False)


def toggle_details(n_clicks, is_open):
    """
    Opens and closes the dropdown showing the full
    original error.
    :param n_clicks: the number of clicks of the details button
    :param is_open: if the dropdown is currently open
    :returns: if the dropdown is open, and the label for
    the details button
    """
    show = not is_open
    return show, HIDE_DETAILS if show else SHOW_DETAILS


def error_details(err):
    """
    The full text of the original error, for the details
    dropdown. If the error was raised from another one
    (raise GUIError(...) from err) then the original is
    reported, as that is the error that says what actually
    went wrong.
    :param err: the exception raised by the callback
    :returns: the traceback of the error as a string
    """
    original = err.__cause__ or err
    return ''.join(traceback.format_exception(type(original),
                                              original,
                                              original.__traceback__))


def display_error(err):
    """
    The global callback error handler. Instead of the
    exception only reaching the terminal, it is shown
    in the alert at the top of the GUI. The readable
    message is always visible and the full error is
    in the details dropdown.

    Errors that are not GUIErrors have no message for
    the user, so they only get a generic one.
    :param err: the exception raised by the callback
    """
    msg = UNEXPECTED_MSG
    if isinstance(err, GUIError):
        for component_id, props in err.revert.items():
            set_props(component_id, props)
        msg = str(err)

    set_props(MSG, {'children': ERROR_PREFIX + msg})
    set_props(DETAILS, {'children': error_details(err)})
    # a new error starts with its details hidden
    set_props(DETAILS_COLLAPSE, {'is_open': False})
    set_props(DETAILS_BTN, {'children': SHOW_DETAILS})
    set_props(ALERT, {'is_open': True})
