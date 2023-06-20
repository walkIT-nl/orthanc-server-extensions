import asyncio
import time
from functools import partial

from orthanc_ext.executor_utilities import SequentialHybridExecutor, AsyncOnlyExecutor
from tests.test_event_dispatcher import ChangeEvent


def test_SequentialHybridExecutor_should_invoke_both_sync_async_handlers_and_return_the_result():
    s_client = object()
    a_client = object
    dispatcher = SequentialHybridExecutor(s_client, a_client)
    change_event = ChangeEvent()
    start = time.perf_counter()
    assert dispatcher.invoke_all(
        change_event, [lambda event, client: (42, event, client)],
        [partial(long_async_func, 43)]) == [(42, change_event, s_client),
                                            (43, change_event, a_client)]
    end = time.perf_counter()
    assert end - start > 0.5, 'invoke_all should wait for async function completion'


async def long_async_func(ret_val, event, client):
    await asyncio.sleep(0.5)
    return ret_val, event, client


def long_sync_func(ret_val, event, client):
    time.sleep(0.5)
    return ret_val, event, client


def test_AsyncOnlyExecutor_shall_handle_events_as_they_come_in():
    a_client = object()
    s_client = object()
    dispatcher = AsyncOnlyExecutor(s_client, a_client)
    dispatcher.start()
    change_event1 = ChangeEvent()
    change_event2 = ChangeEvent()
    change_event2.resource_id = 'resource-uuid2'

    start = time.perf_counter()

    task1, _ = dispatcher.invoke_all(change_event1, [], [partial(long_async_func, 42)])
    sync_task1, = dispatcher.invoke_all(change_event2, [partial(long_sync_func, 40)], [])
    end = time.perf_counter()

    task2, _ = dispatcher.invoke_all(change_event2, [], [partial(long_async_func, 43)])

    assert task1.result() == [(42, change_event1, a_client)]
    assert task2.result() == [(43, change_event2, a_client)]
    while not sync_task1.done():
        time.sleep(0.1)
    assert sync_task1.result() == [(40, change_event2, s_client)]

    assert end - start < 0.01, 'invoke_all should never block'


def test_AsyncOnlyExecutor_shall_report_exceptions_with_traceback(caplog):
    a_client = object()
    dispatcher = AsyncOnlyExecutor(None, a_client)
    dispatcher.start()
    change_event1 = ChangeEvent()
    change_event2 = ChangeEvent()
    change_event2.resource_id = 'resource-uuid2'

    async def failing_func(ex, *_):
        raise ex

    ex = Exception('failed')
    task1, sync_task_empty = dispatcher.invoke_all(change_event1, [], [partial(failing_func, ex)])
    assert task1.result() == [ex]
    assert sync_task_empty.result() == []

    assert "execution of coroutine 'failing_func' failed with exception" in caplog.records[
        0].message
    assert "Exception('failed')" in caplog.records[0].message


def test_AsyncOnlyExecutor_shall_report_pending_tasks_on_stop(caplog):
    a_client = object()
    dispatcher = AsyncOnlyExecutor(None, a_client)
    dispatcher.start()
    sync_task1, = dispatcher.invoke_all(ChangeEvent(), [partial(long_sync_func, 40)], [])
    dispatcher.stop()
    assert sync_task1.cancelled()
    assert 'about to stop event loop with 1 task(s) pending: ' \
           "{<Task pending name='sync_handlers[" in caplog.records[0].message
    assert not dispatcher.thread.is_alive()
