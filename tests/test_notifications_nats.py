from contextlib import closing

import pytest
from dockercontext import container as containerlib
import nats


@pytest.fixture(scope='session')
def nats_server():
    with containerlib.Context('nats:latest', {'4222/tcp': 54222}) as container:
        yield container


@pytest.mark.asyncio
async def test_response(nats_server):
    with closing(await nats.connect('localhost:54222')) as nc:
        sub = await nc.subscribe('foo')

        await nc.publish('foo', b'Hello from Python!')

        msg = await sub.next_msg(timeout=2)
        assert msg.subject == 'foo'
        print('Received:', msg)
