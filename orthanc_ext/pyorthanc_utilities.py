from enum import Enum
from typing import Union

import httpx
from pyorthanc import Orthanc, AsyncOrthanc


class ClientType(Enum):
    SYNC = Orthanc
    ASYNC = AsyncOrthanc

    @staticmethod
    def create_internal_client(*args, **kwargs):
        return create_internal_client(*args, **kwargs)


def create_internal_client(
        base_url,
        token='',
        cert: Union[str, bool] = False,
        client_type: ClientType = ClientType.SYNC):
    return client_type.value(
        base_url,
        base_url=base_url,
        timeout=httpx.Timeout(300, connect=30),
        verify=cert,
        headers={'Authorization': token})
