from collections.abc import Iterable


def ensure_iterable(v):
    return v if isinstance(v, Iterable) else [v]


def register_event_handlers(event_handlers, orthanc_module):
    event_types = {v: k for k, v in orthanc_module.ChangeType.__dict__.items()}
    event_handlers = {k: ensure_iterable(v) for k, v in event_handlers.items()}

    def unhandled_event_logger(change_type: orthanc_module.ChangeType, level, resource_id, orthanc):
        orthanc.LogInfo(f'no handler registered for {event_types[change_type]}')

    def OnChange(change_type, level, resource_id):
        handlers = event_handlers.get(change_type, [unhandled_event_logger])
        for handler in handlers:
            handler(change_type, level, resource_id, orthanc=orthanc_module)

    orthanc_module.RegisterOnChangeCallback(OnChange)
