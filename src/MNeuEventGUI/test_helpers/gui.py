import time

from MNeuEventGUI.utils.errors import MODAL, MSG


def check_no_error_popup(dash_duo):
    """
    Checks that the error pop up has not opened,
    which is what should happen when everything works.
    :param dash_duo: the dash test browser
    :raises AssertionError: if the pop up is on screen
    """
    # the pop up is only added to the page when it is open,
    # so there is usually nothing to find
    popups = [popup for popup in dash_duo.find_elements('#' + MODAL)
              if popup.is_displayed()]
    assert not popups, ('the error pop up has opened: '
                        + dash_duo.find_element('#' + MSG).text)

def wait_and_press_btn(dash_duo, name):
    """
    Method to wait for the loading to
    complete and then click an element
    (button).
    :param dash_duo:
    :param name: the name/ID of the button
    """
    active = False
    while not active:
        try:
            dash_duo.find_element('#' + name).click()
            active = True
        except Exception:
            time.sleep(.1)
