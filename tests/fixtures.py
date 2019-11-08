import asynctest
from unittest.mock import MagicMock


class AIONetboxResponseMock():
    pass


class AIONetboxMagicMock(MagicMock):

    request = asynctest.CoroutineMock(return_value=AIONetboxResponseMock())
    close = asynctest.CoroutineMock()


class AIONetboxMock():

    _attrs = {}

    request = asynctest.CoroutineMock(return_value=AIONetboxResponseMock())
    close = asynctest.CoroutineMock()

    def __init__(*args, **kwargs):
        pass

    def __setattr__(self, attr, value):
        self._attrs[attr] = value

    def __getattr__(self, attr):

        ret = self._attrs.get(attr, MagicMock())

        if isinstance(ret, Exception):
            raise ret

        return ret
