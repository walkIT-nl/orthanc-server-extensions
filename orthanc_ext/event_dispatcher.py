import asyncio
import inspect
import json
import logging
from dataclasses import dataclass

from orthanc_ext.http_utilities import create_internal_client, get_rest_api_base_url, \
    get_certificate
from orthanc_ext.logging_configurator import python_logging
from orthanc_ext.python_utilities import ensure_iterable, create_reverse_type_dict


def register_event_handlers(
        event_handlers, orthanc_module, requests_session, logging_configuration=python_logging):
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
        return await asyncio.gather(*async_handlers)

    def OnChange(change_type, resource_type, resource_id):
        event = ChangeEvent(change_type, resource_type, resource_id)
        awaitable_or_return_value = [
            handler(event, requests_session)
            for handler in event_handlers.get(change_type, [unhandled_event_logger])
        ]

        return_values = [
            handler for handler in awaitable_or_return_value if not inspect.isawaitable(handler)
        ]
        async_handlers = [
            handler for handler in awaitable_or_return_value if inspect.isawaitable(handler)
        ]

        return return_values + asyncio.run(on_change_async(async_handlers))

    orthanc_module.RegisterOnChangeCallback(OnChange)


def create_session(orthanc):
    config = json.loads(orthanc.GetConfiguration())
    return create_internal_client(
        get_rest_api_base_url(config), orthanc.GenerateRestApiAuthorizationToken(),
        get_certificate(config))
