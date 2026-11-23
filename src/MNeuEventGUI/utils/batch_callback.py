"""
Helpers for callbacks on widgets that are repeated for each batch.

Batches can be added while the GUI is running, but Dash callbacks
can only be registered before it starts. So each batch's components
have pattern matching IDs ({'type': name, 'batch': key}), and their
callbacks are registered once with MATCH in place of the batch.
One callback then serves every batch, including later ones.

A MATCH callback is registered with the first batch's presenter, so
dispatch wraps the method: when called, it finds the batch MATCH
resolved to and calls the same method on that batch's presenter
(looked up in the registry filled by register). Methods passed to
dispatch should not rely on the state of the first presenter.

IDs use the batch key, which does not change, rather than the index,
which does when an earlier batch is removed. So removing a batch
leaves the other batches' components untouched.

Callbacks that use every batch (ALL) get their values in page order,
which is not reliably batch order. ordered_callback reorders the ALL
inputs into batch order, and the ALL outputs back into page order,
so presenters can use the batch index.
"""
from dash import callback, ctx, no_update
from dash.exceptions import PreventUpdate

# the presenters for each batch, keyed by
# (presenter type, presenter ID) then by batch key
_REGISTRY = {}


def _kind(presenter):
    """
    :param presenter: a presenter
    :returns: the registry key for this type of presenter
    """
    return type(presenter), presenter.ID


def register(presenter):
    """
    Records the presenter for its batch, so that the
    batch's callbacks are passed on to it.
    :param presenter: the presenter (for a batch)
    """
    _REGISTRY.setdefault(_kind(presenter), {})[presenter.key] = presenter


def unregister_batch(key):
    """
    Forgets all of the presenters for a batch,
    when the batch is removed.
    :param key: the key of the batch
    """
    for presenters in _REGISTRY.values():
        presenters.pop(key, None)


def registered(presenter):
    """
    :param presenter: a presenter (for a batch)
    :returns: the presenter of the same type that is
    currently registered for its batch
    """
    return _REGISTRY.get(_kind(presenter), {}).get(presenter.key)


def _find_batch(specs):
    """
    Finds the batch key in the IDs of a callback's
    dependencies, as reported by the callback context.
    :param specs: the dependencies (a dict, or nested lists of them)
    :returns: the batch key, or None if there is not one
    """
    if isinstance(specs, dict):
        component_id = specs.get('id')
        if isinstance(component_id, dict) and 'batch' in component_id:
            return component_id['batch']
        return None
    for spec in specs or []:
        batch = _find_batch(spec)
        if batch is not None:
            return batch
    return None


def current_batch():
    """
    Gets the key of the batch for the running callback.
    This is the batch the MATCH wildcard was resolved to.
    :returns: the batch key, or None if there is not one
    """
    for specs in (ctx.outputs_list, ctx.inputs_list, ctx.states_list):
        batch = _find_batch(specs)
        if batch is not None:
            return batch
    return None


def dispatch(method):
    """
    Gets the function to use as a callback for a
    presenter's method. For a widget that is shared
    by all batches this is just the method. For a
    batch's widget, the callback calls the method on
    the presenter for the batch that triggered it.
    :param method: the method of a presenter
    :returns: the callback function
    """
    presenter = method.__self__
    if presenter.batch is None:
        return method
    kind = _kind(presenter)
    name = method.__name__

    def handler(*args):
        target = _REGISTRY.get(kind, {}).get(current_batch())
        if target is None:
            # the batch has been removed
            raise PreventUpdate
        return getattr(target, name)(*args)

    return handler


def _keys(specs):
    """
    :param specs: the matched components of an ALL dependency
    :returns: the batch keys of the components, in page order
    """
    return [spec['id']['batch'] for spec in specs]


def to_batch_order(value, specs, order):
    """
    Puts the values of an ALL dependency into batch order.
    :param value: the values, in page order
    :param specs: the matched components, in page order
    :param order: the batch keys, in batch order
    :returns: the values, in batch order
    """
    by_key = dict(zip(_keys(specs), value))
    return [by_key.get(key) for key in order]


def to_page_order(value, specs, order):
    """
    Puts the values for an ALL output into page order.
    :param value: the values, in batch order
    :param specs: the matched components, in page order
    :param order: the batch keys, in batch order
    :returns: the values, in page order
    """
    if value is no_update:
        return value
    by_key = dict(zip(order, value))
    return [by_key.get(key, no_update) for key in _keys(specs)]


def ordered_callback(order, output, inputs, state=(), **kwargs):
    """
    Registers a callback that uses ALL wildcards. Its
    function gets, and returns, the values for every
    batch in batch order, whatever the page order is.
    :param order: a function that returns the batch keys,
    in batch order
    :param output: the Output (or list of them)
    :param inputs: the list of Inputs
    :param state: the list of States
    :param kwargs: any other arguments for the callback
    :returns: a decorator for the callback function
    """
    single_output = not isinstance(output, (list, tuple))

    def decorator(func):
        def wrapped(*args):
            keys = order()
            specs = list(ctx.inputs_list) + list(ctx.states_list)
            args = [to_batch_order(arg, spec, keys)
                    if isinstance(spec, list) else arg
                    for arg, spec in zip(args, specs)]

            result = func(*args)

            outputs = ctx.outputs_list
            if single_output:
                return (to_page_order(result, outputs, keys)
                        if isinstance(outputs, list) else result)
            return [to_page_order(value, spec, keys)
                    if isinstance(spec, list) else value
                    for value, spec in zip(result, outputs)]

        callback(output, list(inputs), list(state), **kwargs)(wrapped)
        return func

    return decorator
