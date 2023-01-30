=========================
Orthanc Server Extensions
=========================


.. image:: https://img.shields.io/pypi/v/orthanc-server-extensions.svg
        :target: https://pypi.python.org/pypi/orthanc-server-extensions

.. image:: https://travis-ci.com/walkIT-nl/orthanc-server-extensions.svg?branch=main
        :target: https://travis-ci.com/walkIT-nl/orthanc-server-extensions

.. image:: https://readthedocs.org/projects/orthanc-server-extensions/badge/?version=latest
        :target: https://orthanc-server-extensions.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://github.com/walkIT-nl/orthanc-server-extensions/actions/workflows/main.yml/badge.svg
        :target: https://github.com/walkIT-nl/orthanc-server-extensions/actions/workflows/main.yml
        :alt: Build and test status

A simple Orthanc python plugin based event processing framework to extend Orthanc’s feature set. It focuses on
integration and orchestration, like study routing, event notifications and audit logging.


* Free software: GNU Affero General Public License v3
* Documentation: https://orthanc-server-extensions.readthedocs.io.


Features
--------
* easily plug event handling scripts for all Orthanc's `change events`_ -
* chain functions into a pipeline (composition)
* run asyncio functions (coroutines) for concurrent processing of a change event
* run (integration) tests for your Orthanc python scripts
* publish events to Kafka, RabbitMQ and NATS

Modules
-------
* auto_retries: retry failed jobs
* auto_forward: forward DICOM to external systems based on python match functions
* anonymization: anonymize DICOM Series using the Orthanc API

Why this library was written
----------------------------

Improve developer happiness: the development roundtrip is just a little bit long to build, run and test a function, even with Docker.
With this library, you can start from the unit tests, move to integration tests, and then deploy the result in the Docker image.

Enable testability: the Orthanc API is provided as a module which is not easy to mock in a clean way.
Orthanc server extensions provide a few simple abstractions that keep functions clean and independently testable.

Improve performance: async functions will be executed concurrently, which is advantageous if the processing is I/O bound.

Httpx was chosen as a base library to access the Orthanc API, rather than orthanc.RestApi*, because it is well known,
developer friendly, and external API access avoids deadlocks in the Python plugin (before this was solved in 3.1).


Running
-------

``entry_point.py`` provides the first boilerplate to get started. Run it by issuing
``docker-compose up --build``; you should be greeted with 'orthanc started event handled!' message, which is also published to

Developing
----------

Write your event handling scripts and register them in ``event_dispatcher.register_event_handlers()``. Examples,
including the use of async functions and function composition (pipeline), can be found in ``tests/test_event_dispatcher.py``.


Credits
-------

This project would obviously not exist without Orthanc, its documentation and its community.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _change events: https://book.orthanc-server.com/plugins/python.html#listening-to-changes).
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
