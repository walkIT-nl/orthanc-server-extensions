import asyncio
import logging
from threading import Thread


class AsyncOnlyExecutor:
    """
    Delegates sync handlers to an executor, mimicking async execution.
    Executes async handlers in an event loop that runs in a separate thread.

    For optimal performance, use of only async handlers is preferable.

    This executor needs to be started and stopped.
    """

    def __init__(self, sync_client, async_client):
        self.sync_client = sync_client
        self.async_client = async_client
        self.loop = asyncio.new_event_loop()

        self.tasks = set()  # make sure tasks are not garbage collected

        def run_loop(loop):
            asyncio.set_event_loop(self.loop)
            try:
                loop.run_forever()
            finally:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()

        self.thread = Thread(target=run_loop, args=(self.loop, ), daemon=True)

    def invoke_all(self, event, sync_handlers, async_handlers):
        tasks = [
            asyncio.run_coroutine_threadsafe(
                on_change_async(inject_with_event_http_client(
                    [handler], event, self.async_client)), self.loop) for handler in async_handlers
        ]

        tasks.append(
            self.loop.create_task(
                asyncio.to_thread(
                    inject_with_event_http_client, sync_handlers, event, self.sync_client),
                name=f'sync_handlers{sync_handlers}'))

        self.tasks.update(tasks)
        for task in tasks:
            task.add_done_callback(self.tasks.discard)

        return tasks

    def start(self):
        self.thread.start()

    def stop(self):
        if self.tasks:
            logging.warning(
                'about to stop event loop with %i task(s) pending: %s', len(self.tasks), self.tasks)
        pending = asyncio.all_tasks(self.loop)
        for task in pending:
            task.cancel()

        asyncio.run_coroutine_threadsafe(stop_event_loop_in_thread(self.loop), self.loop)
        self.thread.join()


async def stop_event_loop_in_thread(loop):
    logging.info('stopping event loop')
    loop.stop()


def inject_with_event_http_client(handlers, event, client):
    return [handler(event, client) for handler in handlers]


class SequentialHybridExecutor:
    """Blocking event executor that handles both sync and async handlers,
        returning the gathered results in a list.
        It waits for all async handlers to have completed per received event.
    """

    def __init__(self, sync_client, async_client):
        self.sync_client = sync_client
        self.async_client = async_client

    def invoke_all(self, event, sync_handlers, async_handlers):
        return inject_with_event_http_client(sync_handlers, event, self.sync_client) + asyncio.run(
            on_change_async(
                inject_with_event_http_client(async_handlers, event, self.async_client)))


async def on_change_async(async_handlers):
    return_values = await asyncio.gather(*async_handlers, return_exceptions=True)

    for index, return_value in enumerate(return_values):
        if isinstance(return_value, BaseException):
            logging.exception(
                'execution of coroutine \'%s\' failed with exception %s',
                async_handlers[index].__name__,
                repr(return_value),
                exc_info=(return_value.__class__, return_value, return_value.__traceback__))

    return return_values
