import unittest
from unittest import mock

from MNeuEventGUI.utils.errors import (
    ALERT,
    DETAILS,
    DETAILS_BTN,
    DETAILS_COLLAPSE,
    ERROR_PREFIX,
    HIDE_DETAILS,
    MSG,
    SHOW_DETAILS,
    UNEXPECTED_MSG,
    GUIError,
    display_error,
    error_details,
    toggle_details,
)


def caused_error(msg, revert=None):
    """
    A GUIError raised from an original error, as the
    GUI does when it cannot do what was asked.
    :param msg: the message for the user
    :param revert: the props to put back
    :returns: the GUIError, with a traceback
    """
    try:
        try:
            raise RuntimeError('the original error')
        except RuntimeError as original:
            raise GUIError(msg, revert) from original
    except GUIError as error:
        return error


def catch(error):
    """
    Gives an error a traceback, as it would have when
    it reaches the error handler.
    :param error: the error to raise
    :returns: the same error, with a traceback
    """
    try:
        raise error
    except type(error) as raised:
        return raised


class ErrorsTest(unittest.TestCase):

    def test_error_details_uses_original_error(self):
        """
        If an error was raised from another one, the
        original is the one that explains what happened.
        """
        details = error_details(caused_error('Nice message'))

        self.assertTrue('RuntimeError: the original error' in details)
        self.assertTrue('Nice message' not in details)

    def test_error_details_without_a_cause(self):
        error = catch(GUIError('Nice message'))

        details = error_details(error)

        self.assertTrue('GUIError: Nice message' in details)

    @mock.patch('MNeuEventGUI.utils.errors.set_props')
    def test_display_error_shows_message_and_details(self, set_props):
        display_error(caused_error('Nice message'))

        props = dict(call[0] for call in set_props.call_args_list)

        self.assertEqual(props[MSG],
                         {'children': ERROR_PREFIX + 'Nice message'})
        self.assertTrue('the original error'
                        in props[DETAILS]['children'])
        self.assertEqual(props[ALERT], {'is_open': True})

    @mock.patch('MNeuEventGUI.utils.errors.set_props')
    def test_display_error_hides_details_of_a_new_error(self, set_props):
        display_error(catch(GUIError('Nice message')))

        props = dict(call[0] for call in set_props.call_args_list)

        self.assertEqual(props[DETAILS_COLLAPSE], {'is_open': False})
        self.assertEqual(props[DETAILS_BTN], {'children': SHOW_DETAILS})

    @mock.patch('MNeuEventGUI.utils.errors.set_props')
    def test_display_error_reverts_props(self, set_props):
        error = catch(GUIError('Nice message',
                               {'time-table': {'rowData': [1, 2]}}))

        display_error(error)

        props = dict(call[0] for call in set_props.call_args_list)
        self.assertEqual(props['time-table'], {'rowData': [1, 2]})

    @mock.patch('MNeuEventGUI.utils.errors.set_props')
    def test_display_error_generic_message_for_other_errors(self, set_props):
        """
        Only a GUIError has a message meant for the user,
        anything else gets a generic one (the real error is
        still in the details).
        """
        display_error(catch(KeyError('rowData')))

        props = dict(call[0] for call in set_props.call_args_list)

        self.assertEqual(props[MSG],
                         {'children': ERROR_PREFIX + UNEXPECTED_MSG})
        self.assertTrue("KeyError: 'rowData'" in props[DETAILS]['children'])

    def test_toggle_details_opens(self):
        self.assertEqual(toggle_details(1, False), (True, HIDE_DETAILS))

    def test_toggle_details_closes(self):
        self.assertEqual(toggle_details(2, True), (False, SHOW_DETAILS))


if __name__ == '__main__':
    unittest.main()
