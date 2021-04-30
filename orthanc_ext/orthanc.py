"""
This module implements the Orthanc Python plugin API to run requests against an
external Orthanc instance.

This will allow you quickly evolve your python scripts and make them easy to
integration test as well.
"""
import uuid


class OrthancApiHandler(object):
    class ResourceType:
        PATIENT = 0
        STUDY = 1
        SERIES = 2
        INSTANCE = 3
        NONE = 4

    # Redefine to make this type available for unit tests 
    # outside the Orthanc Python plugin.
    # https://hg.orthanc-server.com/orthanc-python/file/tip/\
    #   Sources/Autogenerated/sdk_OrthancPluginChangeType.impl.h
    class ChangeType:
        COMPLETED_SERIES = 0
        DELETED = 1
        NEW_CHILD_INSTANCE = 2
        NEW_INSTANCE = 3
        NEW_PATIENT = 4
        NEW_SERIES = 5
        NEW_STUDY = 6
        STABLE_PATIENT = 7
        STABLE_SERIES = 8
        STABLE_STUDY = 9
        ORTHANC_STARTED = 10
        ORTHANC_STOPPED = 11
        UPDATED_ATTACHMENT = 12
        UPDATED_METADATA = 13
        UPDATED_PEERS = 14
        UPDATED_MODALITIES = 15
        JOB_SUBMITTED = 16
        JOB_SUCCESS = 17
        JOB_FAILURE = 18

        # not defined by orthanc
        UNKNOWN = 999

    @staticmethod
    def GenerateRestApiAuthorizationToken():
        return uuid.uuid4()

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
