=====
Usage
=====

To use Orthanc Server Extensions in an integration project, the following snippet can serve as the entrypoint script
specified in orthanc.json or as an environment variable for the Osimis docker image (ORTHANC__PYTHON_SCRIPT)::

    import logging
    import orthanc # provided by the Orthanc plugin
    from orthanc_ext import event_dispatcher

    # to prevent the import dependency on orthanc above, normally this would be defined in a separate module
    def log_event(evt, session):
       logging.warn(evt.resource_id)

    event_dispatcher.register_event_handlers({orthanc.ChangeType.STABLE_STUDY: log_event}, orthanc_module=orthanc,
                                             session=event_dispatcher.create_session(orthanc))

To unit test the log_event handler with pytest, use::

    from orthanc_ext.orthanc import OrthancApiHandler
    event_dispatcher.register_event_handlers({orthanc.ChangeType.STABLE_STUDY: log_event}, orthanc_module=OrthancApiHandler(),
                                             session=requests)
    def test_shall_log_on_change(caplog):
        orthanc.on_change(orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, "resource-uuid")

        assert 'resource-uuid' in caplog.text

One can use the excellent responses_ library to stub the API responses.

To integration test a handler, use::

    from orthanc_ext.orthanc import OrthancApiHandler
    from requests_toolbelt import sessions

    orthanc = OrthancApiHandler()
    session = sessions.BaseUrlSession('http://your-orthanc-server:8042')
    session.auth = ('orthanc', 'orthanc')

    def get_system_status(_, session):
        # this would be the session created above
        # BaseUrlSession allows usage equivalent to RestApiPost
        return session.get('/system').json()

    event_dispatcher.register_event_handlers({orthanc.ChangeType.ORTHANC_STARTED: get_system_status}, orthanc_module=orthanc,
                                             session=session)

    def test_get_system_status_shall_return_version():
        system_info, = orthanc.on_change(orthanc.ChangeType.ORTHANC_STARTED, orthanc.ResourceType.NONE, '')

        assert system_info.get('Version') is not None

The event_dispatcher will ensure that your API call will work the same when called from the Orthanc Python plugin.
For more examples, see the tests/ directory in the Git repository.

.. _responses: https://github.com/getsentry/responses
