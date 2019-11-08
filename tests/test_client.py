
import pytest
import asynctest

from unittest.mock import patch

from prophetess_netbox.client import NetboxClient
from prophetess_netbox.exceptions import InvalidPKConfig, InvalidNetboxEndpoint, InvalidNetboxOperation
from .fixtures import AIONetboxMock, AIONetboxMagicMock, AIONetboxResponseMock


@patch('prophetess_netbox.client.AIONetbox')
def test_NetboxClient(maionb):
    NetboxClient(host='http://test', api_key='key')

    maionb.from_openapi.assert_called_with(
        url='http://test',
        api_key='key'
    )


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox', new_callable=AIONetboxMagicMock)
async def test_NetboxClient_close(maionb):
    nb = NetboxClient(host='http://test', api_key='key')

    await nb.close()

    maionb.close.assert_called_once()


@patch('prophetess_netbox.client.AIONetbox', new_callable=AIONetboxMagicMock)
def test_NetboxClient_build_model(maionb):
    nb = NetboxClient(host='http://test', api_key='key')
    client = maionb.from_openapi.return_value
    model = nb.build_model('api', 'test', 'get')

    assert model == client.api.api_test_get


@patch('prophetess_netbox.client.AIONetbox', new_callable=AIONetboxMagicMock)
def test_NetboxClient_build_model_invalid_endpoint(maionb):
    maionb.from_openapi = AIONetboxMock
    nb = NetboxClient(host='http://test', api_key='key')
    nb.client.api = AttributeError()

    with pytest.raises(InvalidNetboxEndpoint):
        nb.build_model('api', 'test', 'get')


@patch('prophetess_netbox.client.AIONetbox', new_callable=AIONetboxMock)
def test_NetboxClient_build_model_invalid_operation(maionb):
    maionb.from_openapi = AIONetboxMagicMock

    nb = NetboxClient(host='http://test', api_key='key')

    nb.client.api = AIONetboxMock()
    nb.client.api.api_bad_get = AttributeError()
    with pytest.raises(InvalidNetboxOperation):
        nb.build_model('api', 'bad', 'get')


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox')
async def test_NetboxClient_fetch(__aionb):

    with patch.object(NetboxClient, 'build_model') as mbm:
        mbm.return_value = asynctest.CoroutineMock()

        nb = NetboxClient(host='http://test', api_key='key')
        await nb.fetch(
            endpoint='test',
            model='testing',
            params={
                'foo': 'bar',
                'baz': 'buzz',
            }
        )

        mbm.assert_called_with('test', 'testing', 'list')
        mbm.return_value.assert_called_with(foo='bar', baz='buzz')


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox')
async def test_NetboxClient_fetch_invalid(__aionb):

    with patch.object(NetboxClient, 'build_model') as mbm:
        mbm.return_value.side_effect = [ValueError, TypeError]
        nb = NetboxClient(host='http://test', api_key='key')

        with pytest.raises(ValueError):
            await nb.fetch(endpoint='fake', model='valid', params={})

        with pytest.raises(TypeError):
            await nb.fetch(endpoint='valid', model='fake', params={})


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox')
async def test_NetboxClient_entity(__aionb):

    with patch.object(NetboxClient, 'fetch', new_callable=asynctest.CoroutineMock) as mf:
        mf.return_value = AIONetboxResponseMock()
        mf.return_value.count = 1
        mf.return_value.results = ['test']

        nb = NetboxClient(host='http://test', api_key='key')

        entity = await nb.entity(
            endpoint='test',
            model='testing',
            params={}
        )

        mf.assert_called_with(
            endpoint='test',
            model='testing',
            params={},
        )

        assert entity == 'test'


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox')
async def test_NetboxClient_entity_empty(__aionb):

    with patch.object(NetboxClient, 'fetch', new_callable=asynctest.CoroutineMock) as mf:
        mf.return_value = AIONetboxResponseMock()
        mf.return_value.count = 0

        nb = NetboxClient(host='http://test', api_key='key')

        entity = await nb.entity(
            endpoint='test',
            model='testing',
            params={}
        )

        assert entity is None


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox')
async def test_NetboxClient_entity_too_many(__aionb):

    with patch.object(NetboxClient, 'fetch', new_callable=asynctest.CoroutineMock) as mf:
        mf.return_value = AIONetboxResponseMock()
        mf.return_value.count = 2

        nb = NetboxClient(host='http://test', api_key='key')

        with pytest.raises(InvalidPKConfig):
            await nb.entity(
                endpoint='test',
                model='testing',
                params={}
            )


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox')
async def test_NetboxClient_entities(__aionb):

    with patch.object(NetboxClient, 'fetch', new_callable=asynctest.CoroutineMock) as mf:
        mf.return_value = AIONetboxResponseMock()
        mf.return_value.count = 1
        mf.return_value.results = ['test']

        nb = NetboxClient(host='http://test', api_key='key')

        entity = await nb.entities(
            endpoint='test',
            model='testing',
            params={}
        )

        mf.assert_called_with(
            endpoint='test',
            model='testing',
            params={},
        )

        assert entity == ['test']


@pytest.mark.asyncio
@patch('prophetess_netbox.client.AIONetbox')
async def test_NetboxClient_entities_empty(__aionb):

    with patch.object(NetboxClient, 'fetch', new_callable=asynctest.CoroutineMock) as mf:
        mf.return_value = AIONetboxResponseMock()
        mf.return_value.count = 0

        nb = NetboxClient(host='http://test', api_key='key')

        entity = await nb.entities(
            endpoint='test',
            model='testing',
            params={}
        )

        assert entity is None
