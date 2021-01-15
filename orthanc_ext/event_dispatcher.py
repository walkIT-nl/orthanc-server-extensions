from collections.abc import Iterable
from dataclasses import dataclass


def register_event_handlers(event_handlers, orthanc_module):
    @dataclass
    class ChangeEvent:
        change_type: int
        resource_type: int
        resource_id: str

        def __str__(self):
            return f"ChangeEvent(change_type={event_types.get(self.change_type)}, resource_type={self.resource_type}, resource_id='{self.resource_id}')"

    def ensure_iterable(v):
        return v if isinstance(v, Iterable) else [v]

    def can_hash(k):
        try:
            return hash(k)
        except TypeError:
            return False

    event_types = {v: k for k, v in orthanc_module.ChangeType.__dict__.items() if can_hash(v)}
    event_handlers = {k: ensure_iterable(v) for k, v in event_handlers.items()}

    def unhandled_event_logger(event, orthanc):
        orthanc.LogInfo(f'no handler registered for {event_types[event.change_type]}')

    def OnChange(change_type, resource_type, resource_id):
        handlers = event_handlers.get(change_type, [unhandled_event_logger])
        for handler in handlers:
            event = ChangeEvent(change_type, resource_type, resource_id)
            handler(event, orthanc=orthanc_module)

    orthanc_module.RegisterOnChangeCallback(OnChange)
