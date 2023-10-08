from pyorthanc import Orthanc, AsyncOrthanc

from orthanc_ext.event_dispatcher import create_session
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.pyorthanc_utilities import ClientType


def test_shall_create_sync_client():
    client = ClientType.create_internal_client(base_url='http://localhost:8042')
    assert client is not None
    assert type(client) == Orthanc


def test_shall_create_async_client():
    client = ClientType.create_internal_client(
        base_url='http://localhost:8042', client_type=ClientType.ASYNC)
    assert client is not None
    assert type(client) == AsyncOrthanc


def test_shall_support_create_session_for_backward_compatibility():
    assert create_session(OrthancApiHandler(), ClientType.SYNC) is not None
