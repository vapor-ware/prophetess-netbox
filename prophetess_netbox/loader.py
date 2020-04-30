
import logging
import collections

from aionetbox.api import NetboxResponseObject
from aionetbox.exceptions import AIONetboxException

from prophetess.plugin import Loader
from prophetess_netbox.client import NetboxClient
from prophetess_netbox.exceptions import NetboxOperationFailed


log = logging.getLogger('prophetess.plugins.netbox.loader')

casts = {
    'float': float,
    'int': int,
    'string': str,
}


class NetboxLoader(Loader):
    required_config = (
        'host',
        'api_key',
        'endpoint',
        'model',
        'pk',
    )

    def __init__(self, **kwargs):
        """ NetboxLoader init """
        super().__init__(**kwargs)

        self.update_method = self.config.get('update_method', 'update')
        self.client = NetboxClient(host=self.config.get('host'), api_key=self.config.get('api_key'))

    def sanitize_config(self, config):
        """ Overload Loader.sanitize_config to add additional conditioning """
        config = super().sanitize_config(config)

        for k in ('model', 'endpoint'):
            config[k] = config[k].lower()

        if not isinstance(config['pk'], list):
            config['pk'] = [config['pk']]

        return config

    async def parse_fk(self, record):
        extracts = self.config.get('fk')
        if not extracts or not isinstance(extracts, collections.Mapping):
            return record

        for key, rules in extracts.items():
            if key not in record:
                log.debug('Skipping FK lookup "{}". Not found in record'.format(key))
                continue

            r = await self.client.entity(
                endpoint=rules.get('endpoint'),
                model=rules.get('model'),
                params=self.build_params(rules.get('pk', []), record)
            )

            if not r:
                log.debug('FK lookup for {} ({}) failed, no record found'.format(key, record.get(key)))
                record[key] = None
                continue

            record[key] = r.id

        return record

    def build_params(self, config, record):
        output = {}
        for item in config:
            if isinstance(item, str):
                output[item] = record.get(item)
            elif isinstance(item, collections.Mapping):
                for k, tpl in item.items():
                    output[k] = tpl.format(**record)

        return output

    def sanitize_record(self, record):
        if 'cast' not in self.config:
            return record

        for el, t in self.config['cast'].items():
            if el not in record:
                pass

            if record[el] is None:
                continue

            record[el] = casts.get(t)(record[el])

        return record

    def diff_records(self, cur_record, new_record):
        ''' Build a collection of _just_ changed Fields '''

        changed = {}
        log.debug(f'Comparing {cur_record} with {new_record}')

        # Loop through all newly transformed fields
        for k, v in new_record.items():
            log.debug(f'Checking on {k}')
            cur_value = cur_record.get(k)

            # If it's an embedded netbox response, convert it to a dict
            if isinstance(cur_value, NetboxResponseObject):
                cur_value = cur_value.dict()

            # If the fields don't match perform some validation
            if cur_value != v:

                # If the value types align, or either is a None, we have a changed record!
                if isinstance(cur_value, type(v)) or v is None or cur_value is None:
                    log.debug(f'{k} "{cur_value}" ({type(cur_value)}) does not match "{v}" ({type(v)})')
                    changed[k] = v
                    continue

                # Netbox now returns nested dicts for simple value mappings. We can check if there's an ID field and
                # compare there. This is the case of a linked record where an update takes just the ID but a GET of
                # the object returns the tree of fields
                if isinstance(cur_value, collections.Mapping):
                    if 'id' in cur_value:
                        if cur_value['id'] != v:
                            log.debug(f"{k}.id \"{cur_value['id']}\" ({type(cur_value['id'])})"
                                      "does not match \"{v}\" ({type(v)})")
                            changed[k] = v

        return changed

    async def run(self, record):
        """ Overload Loader.run to execute netbox loading of a record """

        er = await self.client.entity(
            endpoint=self.config.get('endpoint'),
            model=self.config.get('model'),
            params=self.build_params(self.config.get('pk'), record)
        )

        record = await self.parse_fk(record)

        payload = {
            'data': record
        }

        method = 'create'
        if er:
            method = self.update_method
            payload['id'] = er.id

        if method == 'partial_update':
            er = self.sanitize_record(er.dict())
            record = self.sanitize_record(record)
            changed_record = self.diff_records(er, record)
            if not changed_record:
                log.debug('Skipping {} as no data has changed'.format(record))
                return

            payload['data'] = changed_record

        func = self.client.build_model(self.config.get('endpoint'), self.config.get('model'), method)

        log.debug(f'Running {method} with payload: {payload}')
        try:
            return await func(**payload)
        except AIONetboxException as e:
            log.debug(f'Failed to {method}')
            raise NetboxOperationFailed(str(e))

    async def close(self):
        await self.client.close()
