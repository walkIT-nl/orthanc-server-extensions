"""
This module implements the Orthanc Python plugin API to run requests against an external Orthanc instance.

This will allow you quickly evolve your python scripts and make them easy to integration test as well.
"""
import requests
from urllib.parse import urlparse
from enum import auto

import logging


class OrthancApiHandler(object):
    class ChangeType:
        ORTHANC_STARTED = auto()
        ORTHANC_STOPPED = auto()
        UNKNOWN = auto()

    def __init__(self, session=requests.Session()):
        self.session = session
        self.base_url = "https://localhost:8042"

        def default_callback():
            raise NotImplemented("change_callback")

        self.change_callback = default_callback

    def LogWarning(self, message):
        logging.log(logging.WARNING, message)

    def LogInfo(self, message):
        logging.log(logging.INFO, message)

    def HttpPost(self, path, body, headers):
        response = self.session.post(path, body, headers=headers, verify=False)
        response.raise_for_status()
        return response.text

    def RestApiPost(self, path, body):
        calculated_path = f'{self.base_url}{path}'

        response = self.session.post(calculated_path, body, verify=False)
        response.raise_for_status()
        return response.text

    def RestApiGet(self, path):
        response = self.session.get(f'{self.base_url}{path}', verify=False)
        response.raise_for_status()
        return response.text

    def RegisterOnChangeCallback(self, change_callback):
        self.change_callback = change_callback

    def on_change(self, change_type, level, resource_id):
        return self.change_callback(change_type, level, resource_id)
