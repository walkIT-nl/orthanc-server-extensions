from enum import Enum
from typing import Union

import httpx
from pyorthanc import Orthanc, AsyncOrthanc

from orthanc_ext.http_utilities import OrthancClientTypeFactory


class PyOrthancClientType(OrthancClientTypeFactory, Enum):
    SYNC = Orthanc
    ASYNC = AsyncOrthanc

    def create_internal_client(self, *args, **kwargs):
        return create_internal_client(*args, **kwargs, client_type=self)


def create_internal_client(
        base_url,
        token='',
        cert: Union[str, bool] = False,
        client_type: PyOrthancClientType = PyOrthancClientType.SYNC):

    # note: only difference with the httpx.Client constructor is the `base_url` positional argument.
    return client_type.http_client(
        base_url,
        base_url=base_url,
        timeout=httpx.Timeout(300, connect=30),
        verify=cert,
        headers={'Authorization': token})
