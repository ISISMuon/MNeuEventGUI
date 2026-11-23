import unittest
from types import SimpleNamespace
from unittest import mock

from dash import Input, Output, no_update
from dash.exceptions import PreventUpdate

from MNeuEventGUI.utils import batch_callback
from MNeuEventGUI.utils.batch import all_batches, batch_id
from MNeuEventGUI.utils.batch_callback import (
    current_batch,
    dispatch,
    ordered_callback,
    register,
    registered,
    to_batch_order,
    to_page_order,
    triggered_batch,
    unregister_batch,
)

CTX = 'MNeuEventGUI.utils.batch_callback.ctx'


def spec(name, key, prop='value'):
    """
    :returns: a dependency, as reported by the callback context
    """
    return {'id': batch_id(name, key), 'property': prop}


def context(outputs=(), inputs=(), states=(), triggered_id=None,
            triggered=()):
    """
    :returns: a stand in for the callback context
    """
    return SimpleNamespace(outputs_list=list(outputs),
                           inputs_list=list(inputs),
                           states_list=list(states),
                           triggered_id=triggered_id,
                           triggered=list(triggered))


class FakePresenter:
    ID = 'fake'

    def __init__(self, key):
        self.batch = key
        self.key = key

    def method(self, value):
        return (self.key, value)


class SharedPresenter(FakePresenter):
    """
    A presenter that is shared by all batches.
    """
    def __init__(self):
        super().__init__(None)


class BatchCallbackTest(unittest.TestCase):

    def setUp(self):
        self.addCleanup(batch_callback._REGISTRY.clear)

    def test_register(self):
        first = FakePresenter(7)
        register(first)
        self.assertIs(registered(FakePresenter(7)), first)

    def test_unregister_batch(self):
        register(FakePresenter(7))
        register(FakePresenter(8))
        unregister_batch(7)
        self.assertIsNone(registered(FakePresenter(7)))
        self.assertIsNotNone(registered(FakePresenter(8)))

    def test_current_batch_from_output(self):
        ctx = context(outputs=[spec('a', 3)], inputs=[spec('b', 3)])
        with mock.patch(CTX, ctx):
            self.assertEqual(current_batch(), 3)

    def test_current_batch_from_input(self):
        # callbacks without outputs get it from their inputs
        ctx = context(inputs=[spec('b', 4)])
        with mock.patch(CTX, ctx):
            self.assertEqual(current_batch(), 4)

    def test_current_batch_none(self):
        ctx = context(outputs=[{'id': 'plot', 'property': 'figure'}])
        with mock.patch(CTX, ctx):
            self.assertIsNone(current_batch())

    def test_triggered_batch(self):
        ctx = context(triggered_id=batch_id('close', 2),
                      triggered=[{'value': 1}])
        with mock.patch(CTX, ctx):
            self.assertEqual(triggered_batch(), (2, 1))

    def test_triggered_batch_not_clicked(self):
        # a component that has just been created
        ctx = context(triggered_id=batch_id('close', 2),
                      triggered=[{'value': 0}])
        with mock.patch(CTX, ctx):
            self.assertEqual(triggered_batch(), (None, 0))

    def test_triggered_batch_not_a_batch(self):
        ctx = context(triggered_id='add', triggered=[{'value': 1}])
        with mock.patch(CTX, ctx):
            self.assertEqual(triggered_batch(), (None, 0))

    def test_dispatch_shared_presenter(self):
        presenter = SharedPresenter()
        self.assertEqual(dispatch(presenter.method), presenter.method)

    def test_dispatch_to_triggering_batch(self):
        first = FakePresenter(0)
        second = FakePresenter(5)
        register(first)
        register(second)
        # the callback is made with the first batch's presenter
        handler = dispatch(first.method)

        with mock.patch(CTX, context(inputs=[spec('b', 5)])):
            self.assertEqual(handler('x'), (5, 'x'))

    def test_dispatch_removed_batch(self):
        presenter = FakePresenter(0)
        register(presenter)
        handler = dispatch(presenter.method)
        unregister_batch(0)

        ctx = context(inputs=[spec('b', 0)])
        with mock.patch(CTX, ctx), self.assertRaises(PreventUpdate):
            handler('x')

    def test_to_batch_order(self):
        specs = [spec('t', 2), spec('t', 0), spec('t', 1)]
        self.assertEqual(to_batch_order(['c', 'a', 'b'], specs, [0, 1, 2]),
                         ['a', 'b', 'c'])

    def test_to_page_order(self):
        specs = [spec('t', 2), spec('t', 0), spec('t', 1)]
        self.assertEqual(to_page_order(['a', 'b', 'c'], specs, [0, 1, 2]),
                         ['c', 'a', 'b'])

    def test_to_page_order_unknown_batch(self):
        # e.g. a component of a batch that is being removed
        specs = [spec('t', 9), spec('t', 0)]
        self.assertEqual(to_page_order(['a'], specs, [0]),
                         [no_update, 'a'])

    def test_to_page_order_no_update(self):
        self.assertIs(to_page_order(no_update, [spec('t', 0)], [0]),
                      no_update)

    @mock.patch('MNeuEventGUI.utils.batch_callback.callback')
    def test_ordered_callback(self, callback):
        func = mock.Mock(return_value=(['A', 'B'], 'plot'))
        ordered_callback(lambda: [4, 1],
                         [Output(all_batches('t'), 'value'),
                          Output('plot', 'figure')],
                         [Input(all_batches('t'), 'value'),
                          Input('tabs', 'data')])(func)
        wrapped = callback.return_value.call_args[0][0]

        # the page has the batches the other way round
        page = [spec('t', 1), spec('t', 4)]
        ctx = context(outputs=[page, {'id': 'plot'}],
                      inputs=[page, {'id': 'tabs'}])
        with mock.patch(CTX, ctx):
            result = wrapped(['b', 'a'], 'active')

        func.assert_called_once_with(['a', 'b'], 'active')
        self.assertEqual(result, [['B', 'A'], 'plot'])

    @mock.patch('MNeuEventGUI.utils.batch_callback.callback')
    def test_ordered_callback_single_output(self, callback):
        func = mock.Mock(return_value=['A', 'B'])
        ordered_callback(lambda: [4, 1],
                         Output(all_batches('t'), 'value'),
                         [Input('btn', 'n_clicks')])(func)
        wrapped = callback.return_value.call_args[0][0]

        page = [spec('t', 1), spec('t', 4)]
        ctx = context(outputs=page, inputs=[{'id': 'btn'}])
        with mock.patch(CTX, ctx):
            self.assertEqual(wrapped(1), ['B', 'A'])


if __name__ == '__main__':
    unittest.main()
