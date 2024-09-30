import inspect
import json
import logging
from dataclasses import dataclass

from orthanc_ext.executor_utilities import SequentialHybridExecutor
from orthanc_ext.http_utilities import get_rest_api_base_url, \
    get_certificate, OrthancClientTypeFactory, HttpxClientType
from orthanc_ext.logging_configurator import python_logging
from orthanc_ext.python_utilities import ensure_iterable, create_reverse_type_dict


def register_event_handlers(
        event_handlers,
        orthanc_module,
        sync_client,
        async_client=None,
        logging_configuration=python_logging,
        handler_executor=SequentialHybridExecutor):
    logging_configuration(orthanc_module)

    @dataclass
    class ChangeEvent:
        change_type: int
        resource_type: int
        resource_id: str

        def __str__(self):
            return (
                f'ChangeEvent('
                f'change_type={event_types.get(self.change_type)}, '
                f'resource_type={resource_types.get(self.resource_type)}, '
                f"resource_id='{self.resource_id}')")

    def create_type_index(orthanc_type):
        return create_reverse_type_dict(orthanc_type)

    event_types = create_type_index(orthanc_module.ChangeType)
    resource_types = create_type_index(orthanc_module.ResourceType)

    event_handlers = {k: ensure_iterable(v) for k, v in event_handlers.items()}

    executor = handler_executor(sync_client, async_client)

    def unhandled_event_logger(event, _):
        logging.debug(f'no handler registered for {event_types[event.change_type]}')

    def OnChange(change_type, resource_type, resource_id):
        event = ChangeEvent(change_type, resource_type, resource_id)
        handlers = event_handlers.get(change_type, [unhandled_event_logger])

        sync_handlers = get_sync_handlers(handlers)
        async_handlers = get_async_handlers(handlers)

        return executor.invoke_all(event, sync_handlers, async_handlers)

    orthanc_module.RegisterOnChangeCallback(OnChange)

    return executor


def get_async_handlers(handlers):
    return [handler for handler in handlers if inspect.iscoroutinefunction(handler)]


def get_sync_handlers(handlers):
    return [handler for handler in handlers if not inspect.iscoroutinefunction(handler)]


def create_session(orthanc, client_type: OrthancClientTypeFactory = HttpxClientType.SYNC):
    config = json.loads(orthanc.GetConfiguration())
    return client_type.create_internal_client(
        get_rest_api_base_url(config), orthanc.GenerateRestApiAuthorizationToken(),
        get_certificate(config))
