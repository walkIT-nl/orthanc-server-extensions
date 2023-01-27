import asyncio
import inspect
import json
import logging
from dataclasses import dataclass

from orthanc_ext.http_utilities import create_internal_client, get_rest_api_base_url, \
    get_certificate, ClientType
from orthanc_ext.logging_configurator import python_logging
from orthanc_ext.python_utilities import ensure_iterable, create_reverse_type_dict


def register_event_handlers(
        event_handlers,
        orthanc_module,
        sync_client,
        async_client=None,
        logging_configuration=python_logging):
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

    def unhandled_event_logger(event, _):
        logging.debug(f'no handler registered for {event_types[event.change_type]}')

    async def on_change_async(async_handlers):
        return_values = await asyncio.gather(*async_handlers, return_exceptions=True)

        for index, return_value in enumerate(return_values):
            if isinstance(return_value, BaseException):
                logging.exception(
                    'execution of %s failed; %s', async_handlers[index], repr(return_value))

        return return_values

    def get_validated_async_client(async_client):
        if async_client is None:
            raise ValueError('a configured async_client is required when using async handlers')
        return async_client

    def OnChange(change_type, resource_type, resource_id):
        event = ChangeEvent(change_type, resource_type, resource_id)
        handlers = event_handlers.get(change_type, [unhandled_event_logger])

        return_values = [
            handler(event, sync_client)
            for handler in handlers
            if not inspect.iscoroutinefunction(handler)
        ]
        async_handlers = [
            handler(event, get_validated_async_client(async_client))
            for handler in handlers
            if inspect.iscoroutinefunction(handler)
        ]

        return return_values + asyncio.run(on_change_async(async_handlers))

    orthanc_module.RegisterOnChangeCallback(OnChange)


def create_session(orthanc, client_type=ClientType.SYNC):
    config = json.loads(orthanc.GetConfiguration())
    return create_internal_client(
        get_rest_api_base_url(config), orthanc.GenerateRestApiAuthorizationToken(),
        get_certificate(config), client_type)
