# 🧙‍♀️ Prophetess Netbox Plugin

[Prophetess](https://github.com/vapor-ware/prophetess) plugin for loading data into [Netbox](https://github.com/netbox-community/netbox)

# 🚀 Installation

```sh
pip install prophetess-netbox
```

# 🔧 Configuration

[NetboxLoader](/prophetess_netbox/loader.py#L12) takes several required and optional configuration options. The full configuration break down is presented below:

```yaml
host: 'http://localhost:8000'
api_key: 123key
update_method: update
endpoint: dcim
model: sites
pk:
- slug
- cf_id: "{site}"
fk:
  region:
    endpoint: dcim
    model: regions
    pk:
    - cf_sf_id: "{region}"
```

## Loader

| Key           | Values                        | Description  |
| ------------- | ----------------------------- | ----- |
| host          | string                        | Fully qualified URL to root of Netbox install  |
| api_key       | string                        | Valid API key for accessing Netbox resources |
| update_method | (update, partial_update)      | When updating existing records, which method to use. `update` will send all fields, `partial_update` will only submit changed values, or skip the update if no values have been updated  |
| endpoint      | string                        | The root API group to use, eg: dcim, ipam, tenant, etc |
| model         | string                        | Which Model of the endpoint to manipulate |
| pk            | string or list (pk)           | How to identify a unique record from endpoint and model. See [PK](#pk) |
| fk            | object (fk)                   | Mapping of any record fields that are related to other data models. See [FK](#fk) |


## PK

PK, Primary Key(s), are a list of strings or dictionaries (objects) on how to check if a record to be loaded exists. When using a dictionary the key is used for lookup against the API and the value is a Python formatted string. This allows for flexibility in mapping parsed record to what Netbox assumes.

For example, given the parsed record of:

```python
{
  'slug': 'nb-slug',
  'region': 'custom-field-lookup',
  'name': 'test',
}
```

With a PK config of

```yaml
- slug
- cf_region: '{region}'
```

The resulting lookup would be: `?slug=nb-slug&cf_region=custom-field-lookup`

## FK

FK, Forigen Key(s), allow for mapping of string values from an extractor to record ids in netbox. The are a dictionary of record key to a mapping of configuration for lookup. Records can be linked across any endpoint and model within a single Netbox instance.

Given the following record:

```python
{
  'slug': 'nb-slug',
  'region': 'region-slug',
  'name': 'test',
}
```

When parsed with the following FK configuration:

```yaml
region:
  endpoint: dcim
  model: regions
  pk:
  - slug
```

Would produce, assuming there was a region with the slug `region-slug` that had a record ID of 12:

```python
{
  'slug': 'nb-slug',
  'region': 12,
  'name': 'test',
}
```

If no FK record is found, `None` is set instead.

### Config

| Key           | Values                        | Description  |
| ------------- | ----------------------------- | ----- |
| endpoint      | string                        | The root API group to use, eg: dcim, ipam, tenant, etc |
| model         | string                        | Which Model of the endpoint to manipulate |
| pk            | string or list (pk)           | How to identify a unique record from endpoint and model. See [PK](#pk) |


# 🧰 Development

Please fork this project and create a new branch to submit any changes. While not required, it's highly recommended to first create an issue to propose the change you wish to make. Keep pull requests well scoped to one change / feature.

This project uses `tox` + `pytest` to unit test and lint code. Use the following commands to validate your changes aren't breaking:

```sh
tox --cov-report term-missing
tox -e lint
```

# 🎉 Special Thanks

❤️ [Charles Butler](https://github.com/lazypower)  
❤️ [Erick Daniszewski](https://github.com/edaniszewski)  
