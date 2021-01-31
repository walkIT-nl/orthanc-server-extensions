import json
from collections.abc import Iterable
from dataclasses import dataclass
import logging
from requests_toolbelt import sessions


def create_internal_requests_session(base_url, token, cert=False):
    session = sessions.BaseUrlSession(base_url)
    session.headers['Authorization'] = token
    session.verify = cert
    return session


def get_rest_api_base_url(config):
    port = config.get('HttpPort', 8042)
    scheme = 'https' if config.get('SslEnabled', False) else 'http'
    return f'{scheme}://localhost:{port}/'


def get_certificate(config):
    return config.get('SslCertificate', False)


def create_session(orthanc):
    config = json.loads(orthanc.GetConfiguration())
    return create_internal_requests_session(get_rest_api_base_url(config),
                                            orthanc.GenerateRestApiAuthorizationToken(), get_certificate(config))


def register_event_handlers(event_handlers, orthanc_module, requests_session):
    @dataclass
    class ChangeEvent:
        change_type: int
        resource_type: int
        resource_id: str

        def __str__(self):
            return f"ChangeEvent(change_type={event_types.get(self.change_type)}, " \
                   f"resource_type={resource_types.get(self.resource_type)}, resource_id='{self.resource_id}')"

    def ensure_iterable(v):
        return v if isinstance(v, Iterable) else [v]

    def hashable(k):
        try:
            return hash(k)
        except TypeError:
            return False

    def create_type_index(orthanc_type):
        return {v: k for k, v in orthanc_type.__dict__.items() if hashable(v)}

    event_types = create_type_index(orthanc_module.ChangeType)
    resource_types = create_type_index(orthanc_module.ResourceType)

    event_handlers = {k: ensure_iterable(v) for k, v in event_handlers.items()}

    def unhandled_event_logger(event, _):
        logging.info(f'no handler registered for {event_types[event.change_type]}')

    def OnChange(change_type, resource_type, resource_id):
        handlers = event_handlers.get(change_type, [unhandled_event_logger])
        return_values = []
        for handler in handlers:
            event = ChangeEvent(change_type, resource_type, resource_id)
            return_values.append(handler(event, requests_session))
        return return_values

    orthanc_module.RegisterOnChangeCallback(OnChange)
