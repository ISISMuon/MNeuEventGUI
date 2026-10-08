import time


def check_no_error_popup(dash_duo):
    """
    Want to check that the error pop up has
    not opened if everything works.
    This means that the 'error' element
    is not findable. So we use a try
    :input dash_duo:
    """
    try:
        assert (dash_duo.find_element('#error').is_enabled)
        # should not have a pop up, so above should throw
        assert (False)
    except Exception:
        return

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
