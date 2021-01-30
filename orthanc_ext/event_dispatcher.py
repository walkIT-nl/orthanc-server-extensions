import json
from collections.abc import Iterable
from dataclasses import dataclass
import logging
from requests_toolbelt import sessions


def create_internal_requests_session(base_url, token):
    session = sessions.BaseUrlSession(base_url)
    session.headers['Authorization'] = token
    session.verify = False  # internal traffic only
    return session


def get_rest_api_base_url(orthanc):
    conf = json.loads(orthanc.GetConfiguration())
    port = conf.get('HttpPort', 8042)
    scheme = 'https' if conf.get('SslEnabled', False) else 'http'
    return f'{scheme}://localhost:{port}/'


def create_session(orthanc):
    return create_internal_requests_session(get_rest_api_base_url(orthanc), orthanc.GenerateRestApiAuthorizationToken())


def register_event_handlers(event_handlers, orthanc_module, requests_session):
    @dataclass
    class ChangeEvent:
        change_type: int
        resource_type: int
        resource_id: str

        def __str__(self):
            return f"ChangeEvent(change_type={event_types.get(self.change_type)}, resource_type={self.resource_type}, resource_id='{self.resource_id}')"

    def ensure_iterable(v):
        return v if isinstance(v, Iterable) else [v]

    def hashable(k):
        try:
            return hash(k)
        except TypeError:
            return False

    event_types = {v: k for k, v in orthanc_module.ChangeType.__dict__.items() if hashable(v)}
    event_handlers = {k: ensure_iterable(v) for k, v in event_handlers.items()}

    def unhandled_event_logger(event, _):
        logging.info(f'no handler registered for {event_types[event.change_type]}')

    def OnChange(change_type, resource_type, resource_id):
        handlers = event_handlers.get(change_type, [unhandled_event_logger])
        for handler in handlers:
            event = ChangeEvent(change_type, resource_type, resource_id)
            handler(event, requests_session)

    orthanc_module.RegisterOnChangeCallback(OnChange)
