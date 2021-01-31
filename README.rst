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


A simple Orthanc python plugin based framework to extend Orthanc’s feature set with testable python scripts. It focusses on
integration and orchestration scripts, like study routing, event notifications and audit logging.


* Free software: GNU Affero General Public License v3
* Documentation: https://orthanc-server-extensions.readthedocs.io.


Features
--------
* run (integration) tests for your Orthanc python scripts
* currently supports handling of `change events`_

Why this library was written
----------------------------

Improve developer happiness: the development roundtrip is just a little bit long to build, run and test a function, even with Docker.
With this library, you can start from the unit tests, move to integration tests, and then deploy the result in the Docker image.

Enable testability: the Orthanc API is provided as a module which is not easy to mock in a clean way.
Orthanc server extensions provide a few simple abstractions that keep functions clean and independently testable.

Requests was chosen as a base library to access the Orthanc API, rather than orthanc.RestApi*, because it is well known,
developer friendly, and external API access avoids deadlocks in the Python plugin (before this was solved in 3.1).


Running
-------

``docker-compose up --build`` should greet you with 'orthanc started event handled!' message and provides the first boilerplate
to get started.


Credits
-------

This project would obviously not exist without Orthanc, its documentation and its community.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _change events: https://book.orthanc-server.com/plugins/python.html#listening-to-changes).
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
