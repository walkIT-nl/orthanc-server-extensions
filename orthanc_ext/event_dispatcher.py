import dataclasses
import json
import logging

from orthanc_ext.http_utilities import (
    create_internal_client, get_certificate, get_rest_api_base_url)
from orthanc_ext.logging_configurator import orthanc_logging
from orthanc_ext.python_utilities import ensure_iterable
from orthanc_ext.types import ChangeType, ResourceType


@dataclasses.dataclass
class ChangeEvent:
    change_type: int
    resource_type: int
    resource_id: str

    def __str__(self):
        return (
            f'ChangeEvent(change_type={ChangeType(self.change_type)._name_}, '
            f'resource_type={ResourceType(self.resource_type)._name_}, '
            f'resource_id="{self.resource_id}")')


def unhandled_event_logger(event, _):
    logging.error(f'no handler registered for {ChangeType(event.change_type)}')


def register_event_handlers(
        event_handlers, orthanc_module, client, logging_configuration=orthanc_logging):
    logging_configuration(orthanc_module)
    event_handlers = {k: ensure_iterable(v) for k, v in event_handlers.items()}

    def OnChange(change_type, resource_type, resource_id):
        handlers = event_handlers.get(change_type, [unhandled_event_logger])
        return_values = []
        for handler in handlers:
            event = ChangeEvent(change_type, resource_type, resource_id)
            return_values.append(handler(event, client))
        return return_values

    orthanc_module.RegisterOnChangeCallback(OnChange)


def create_client(orthanc):
    config = json.loads(orthanc.GetConfiguration())
    return create_internal_client(
        get_rest_api_base_url(config), orthanc.GenerateRestApiAuthorizationToken(),
        get_certificate(config))
