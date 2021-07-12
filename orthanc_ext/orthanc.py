"""
This module implements the Orthanc Python plugin API to run requests against an
external Orthanc instance.

This will allow you quickly evolve your python scripts and make them easy to
integration test as well.
"""
import uuid
from orthanc_ext.types import ChangeType, ResourceType


class OrthancApiHandler(object):

    ChangeType = ChangeType

    ResourceType = ResourceType

    @staticmethod
    def GenerateRestApiAuthorizationToken():
        return uuid.uuid4().hex

    def RegisterOnChangeCallback(self, change_callback):
        self.change_callback = change_callback

    def on_change(self, change_type, resource_type, resource_id):
        return self.change_callback(change_type, resource_type, resource_id)

    def LogInfo(self, message):
        print(f'INFO: {message}')

    def LogWarning(self, message):
        print(f'WARNING: {message}')

    def LogError(self, message):
        print(f'ERROR: {message}')
