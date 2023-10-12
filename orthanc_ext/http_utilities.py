from dataclasses import dataclass
from enum import Enum
from typing import Union

import httpx


def get_rest_api_base_url(config):
    port = config.get('HttpPort', 8042)
    scheme = 'https' if config.get('SslEnabled', False) else 'http'
    return f'{scheme}://localhost:{port}/'


def get_certificate(config):
    return False if not config.get('SslEnabled', False) else config.get('SslCertificate', False)


@dataclass
class OrthancClientTypeFactory:
    http_client: type

    def create_internal_client(self, *args, **kwargs):
        return create_internal_client(*args, **kwargs, client_type=self)


class HttpxClientType(OrthancClientTypeFactory, Enum):
    SYNC = httpx.Client
    ASYNC = httpx.AsyncClient


# deprecated, for backward compatibility
ClientType = HttpxClientType


def create_internal_client(
        base_url,
        token='',
        cert: Union[str, bool] = False,
        client_type: ClientType = HttpxClientType.SYNC):
    return client_type.http_client(
        base_url=base_url,
        timeout=httpx.Timeout(300, connect=30),
        verify=cert,
        headers={'Authorization': token})
