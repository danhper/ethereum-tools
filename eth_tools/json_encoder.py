from json import JSONEncoder

from web3.types import HexBytes
from web3.datastructures import AttributeDict


class EthJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, HexBytes):
            return o.hex()
        if isinstance(o, AttributeDict):
            return dict(o)
        if isinstance(o, bytes):
            return o.hex()
        return super().default(o)
