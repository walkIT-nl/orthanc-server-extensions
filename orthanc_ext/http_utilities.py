from enum import Enum
from typing import Union

import httpx


def get_rest_api_base_url(config):
    port = config.get('HttpPort', 8042)
    scheme = 'https' if config.get('SslEnabled', False) else 'http'
    return f'{scheme}://localhost:{port}/'


def get_certificate(config):
    return False if not config.get('SslEnabled', False) else config.get('SslCertificate', False)


class ClientType(Enum):
    SYNC = httpx.Client
    ASYNC = httpx.AsyncClient


def create_internal_client(
        base_url,
        token='',
        cert: Union[str, bool] = False,
        client_type: ClientType = ClientType.SYNC) -> httpx.Client:
    return client_type.value(
        base_url=base_url,
        timeout=httpx.Timeout(300, connect=30),
        verify=cert,
        headers={'Authorization': token})
