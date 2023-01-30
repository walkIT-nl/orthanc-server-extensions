#!/usr/bin/env python
"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['httpx', ]

setup_requirements = []

test_requirements = ['pytest>=3', 'respx', ]

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Affero General Public License v3',
    'Natural Language :: English',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
]  # yapf: disable

setup(
    author='WalkIT',
    author_email='code@walkit.nl',
    python_requires='>=3.8',
    classifiers=classifiers,
    description=(
        "An Orthanc python plugin based framework to extend Orthanc's "
        'feature set with testable Python scripts '),
    install_requires=requirements,
    license='GNU Affero General Public License v3',
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='orthanc testing',
    name='orthanc-server-extensions',
    packages=find_packages(include=['orthanc_ext', 'orthanc_ext.*']),
    setup_requires=setup_requirements,
    extras_require={
        'nats-event-publisher': ['cloudevents', 'nats-py'],
        'kafka-event-publisher': ['cloudevents', 'aiokafka'],
        'rabbitmq-event-publisher': ['cloudevents', 'aio-pika']
    },
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/walkIT-nl/orthanc-server-extensions',
    version='3.3.0',
    zip_safe=False,
)
