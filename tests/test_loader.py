
import pytest
import asynctest

from unittest.mock import patch

from aionetbox.api import NetboxResponseObject
from aionetbox.exceptions import AIONetboxException

from prophetess_netbox.loader import NetboxLoader
from prophetess_netbox.exceptions import NetboxOperationFailed
from .fixtures import AIONetboxMagicMock, AIONetboxResponseMock


@patch('prophetess_netbox.loader.NetboxClient')
def test_NetboxLoader(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
    }

    nbl = NetboxLoader(id='nbloader', config=config)

    mnbc.assert_called_with(
        host='http://testing',
        api_key='12test'
    )

    assert nbl.update_method == 'update'


@patch('prophetess_netbox.loader.NetboxClient')
def test_NetboxLoader_sanitize_config(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'DCIM',
        'model': 'Sites',
        'pk': 'slug',
    }

    nbl = NetboxLoader(id='nbloader', config=config)

    sanitized = nbl.sanitize_config(config)

    assert 'dcim' == sanitized['endpoint']
    assert 'sites' == sanitized['model']
    assert ['slug'] == sanitized['pk']


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_parse_fk(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
        'fk': {
            'tenant': {
                'endpoint': 'tenant',
                'model': 'tenants',
                'pk': [
                    {
                        'slug': '{tenant}',
                    },
                ],
            },
        },
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    mnbc.return_value.entity = asynctest.CoroutineMock()
    mnbc.return_value.entity.return_value = AIONetboxResponseMock()
    mnbc.return_value.entity.return_value.id = 1

    ret = await nbl.parse_fk({'id': 'yay', 'tenant': 'fk-lookup-plz'})

    assert {'id': 'yay', 'tenant': 1} == ret

    mnbc.return_value.entity.assert_called_with(
        endpoint='tenant',
        model='tenants',
        params={'slug': 'fk-lookup-plz'},
    )


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_parse_fk_missing(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    ret = await nbl.parse_fk({'foo': 'bar'})

    assert {'foo': 'bar'} == ret


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_parse_fk_failed(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
        'fk': {
            'tenant': {
                'endpoint': 'tenant',
                'model': 'tenants',
                'pk': [
                    {
                        'slug': '{tenant}',
                    },
                ],
            },
        },
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    mnbc.return_value.entity = asynctest.CoroutineMock()
    mnbc.return_value.entity.return_value = None

    ret = await nbl.parse_fk({'id': 'yay', 'tenant': 'fk-lookup-plz'})

    assert {'id': 'yay', 'tenant': None} == ret


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_parse_fk_skip(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
        'fk': {
            'tenant': {
                'endpoint': 'tenant',
                'model': 'tenants',
                'pk': [
                    {
                        'slug': '{tenant}',
                    },
                ],
            },
        },
    }

    nbl = NetboxLoader(id='nbloader', config=config)

    ret = await nbl.parse_fk({'id': 'yay'})

    assert {'id': 'yay'} == ret


@patch('prophetess_netbox.loader.NetboxClient')
def test_NetboxLoader_build_params(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [
            'slug',
            {'foo': '{data}'}
        ],
    }

    record = {
        'slug': 'hello-dolly',
        'data': 'this is foo',
        'not-pk': 'just ignore',
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    params = nbl.build_params(config.get('pk'), record)

    assert {'slug': 'hello-dolly', 'foo': 'this is foo'} == params


@patch('prophetess_netbox.loader.NetboxClient')
def test_NetboxLoader_diff_records(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
        'fk': {
            'tenant': {
                'endpoint': 'tenant',
                'model': 'tenants',
                'pk': [
                    {
                        'slug': '{tenant}',
                    },
                ],
            },
        },
    }

    cur_record = AIONetboxResponseMock()

    cur_record.id = 1
    cur_record.slug = 'hello'
    cur_record.tenant = AIONetboxResponseMock()
    cur_record.tenant.id = 2
    cur_record.tenant.name = 'hey'

    new_record = {
        'id': 1,
        'slug': 'hello',
        'tenant': 2,
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    diff = nbl.diff_records(cur_record, new_record)

    assert {} == diff


@patch('prophetess_netbox.loader.NetboxClient')
def test_NetboxLoader_diff_records_changed(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
        'fk': {
            'tenant': {
                'endpoint': 'tenant',
                'model': 'tenants',
                'pk': [
                    {
                        'slug': '{tenant}',
                    },
                ],
            },
        },
    }

    tenant_output = {
        'id': 2,
        'name': 'hey',
    }

    output = {
        'id': 1,
        'slug': 'hello',
        'tenant': NetboxResponseObject.from_response(data=tenant_output, type='object'),
    }

    cur_record = NetboxResponseObject.from_response(data=output, type='dict')

    new_record = {
        'id': 1,
        'slug': 'goodbye',
        'tenant': 3,
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    diff = nbl.diff_records(cur_record, new_record)

    assert {'slug': 'goodbye', 'tenant': 3} == diff


@patch('prophetess_netbox.loader.NetboxClient')
def test_NetboxLoader_sanitize_record(mnbc):
    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'cast': {
            'latitude': 'float',
        },
        'pk': [],
        'fk': {
            'tenant': {
                'endpoint': 'tenant',
                'model': 'tenants',
                'pk': [
                    {
                        'slug': '{tenant}',
                    },
                ],
            },
        },
    }
    record = {
        'id': 1,
        'latitude': '-80.91000',
        'longitude': '120.00100',
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    sanitized = nbl.sanitize_record(record)

    assert float('-80.91000') == sanitized['latitude']
    assert '120.00100' == sanitized['longitude']


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_run_create(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
    }

    record = {
        'id': 1,
        'slug': 'goodbye',
        'tenant': 3,
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    mnbc.return_value.entity = asynctest.CoroutineMock()
    mnbc.return_value.entity.return_value = None
    mnbc.return_value.build_model.return_value = asynctest.CoroutineMock()

    ret = await nbl.run(record)

    assert mnbc.return_value.build_model.return_value.return_value == ret

    mnbc.return_value.build_model.assert_called_with('dcim', 'sites', 'create')
    mnbc.return_value.build_model.return_value.assert_called_with(data=record)


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_run_update(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'update_method': 'partial_update',
        'pk': [],
    }

    exisiting_record = {
        'id': 1,
        'slug': 'goodbye',
    }

    response_data = {
        'id': 42,
        'slug': 'updateme',
    }

    record = NetboxResponseObject.from_response(data=exisiting_record, type='dict')
    nbl = NetboxLoader(id='nbloader', config=config)
    mnbc.return_value.entity = asynctest.CoroutineMock()
    mnbc.return_value.entity.return_value = NetboxResponseObject.from_response(data=response_data, type='object')
    mnbc.return_value.build_model.return_value = asynctest.CoroutineMock()

    await nbl.run(record)

    mnbc.return_value.build_model.assert_called_with('dcim', 'sites', 'partial_update')
    mnbc.return_value.build_model.return_value.assert_called_with(id=42, data=record)


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_run_update_skip(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'update_method': 'partial_update',
        'pk': [],
    }

    record = {
        'id': 1,
        'slug': 'goodbye',
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    mnbc.return_value.entity = asynctest.CoroutineMock()
    mnbc.return_value.entity.return_value = AIONetboxResponseMock()
    mnbc.return_value.entity.return_value.id = 1
    mnbc.return_value.entity.return_value.slug = 'goodbye'

    assert await nbl.run(record) is None


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient')
async def test_NetboxLoader_run_failed(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
    }

    record = {
        'id': 1,
        'slug': 'goodbye',
        'tenant': 3,
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    mnbc.return_value.entity = asynctest.CoroutineMock()
    mnbc.return_value.entity.return_value = None
    mnbc.return_value.build_model.return_value = asynctest.CoroutineMock()
    mnbc.return_value.build_model.return_value.side_effect = [AIONetboxException()]

    with pytest.raises(NetboxOperationFailed):
        await nbl.run(record)


@pytest.mark.asyncio
@patch('prophetess_netbox.loader.NetboxClient', new_callable=AIONetboxMagicMock)
async def test_NetboxLoader_close(mnbc):

    config = {
        'host': 'http://testing',
        'api_key': '12test',
        'endpoint': 'dcim',
        'model': 'sites',
        'pk': [],
    }

    nbl = NetboxLoader(id='nbloader', config=config)
    await nbl.close()

    mnbc.return_value.close.assert_called()
