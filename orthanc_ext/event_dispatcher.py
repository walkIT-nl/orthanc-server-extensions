import json
import logging

from dataclasses import dataclass

from orthanc_ext.logging_configurator import configure_orthanc_log_format
from orthanc_ext.python_utilities import ensure_iterable, create_reverse_type_dict
from orthanc_ext.requests_utilities import create_internal_requests_session, get_rest_api_base_url, get_certificate

configure_orthanc_log_format()


def register_event_handlers(event_handlers, orthanc_module, requests_session):
    @dataclass
    class ChangeEvent:
        change_type: int
        resource_type: int
        resource_id: str

        def __str__(self):
            return f"ChangeEvent(change_type={event_types.get(self.change_type)}, " \
                   f"resource_type={resource_types.get(self.resource_type)}, resource_id='{self.resource_id}')"

    def create_type_index(orthanc_type):
        return create_reverse_type_dict(orthanc_type)

    event_types = create_type_index(orthanc_module.ChangeType)
    resource_types = create_type_index(orthanc_module.ResourceType)

    event_handlers = {k: ensure_iterable(v) for k, v in event_handlers.items()}

    def unhandled_event_logger(event, _):
        logging.debug(f'no handler registered for {event_types[event.change_type]}')

    def OnChange(change_type, resource_type, resource_id):
        handlers = event_handlers.get(change_type, [unhandled_event_logger])
        return_values = []
        for handler in handlers:
            event = ChangeEvent(change_type, resource_type, resource_id)
            return_values.append(handler(event, requests_session))
        return return_values

    orthanc_module.RegisterOnChangeCallback(OnChange)


def create_session(orthanc):
    config = json.loads(orthanc.GetConfiguration())
    return create_internal_requests_session(get_rest_api_base_url(config),
                                            orthanc.GenerateRestApiAuthorizationToken(), get_certificate(config))
