import csv
from functools import wraps

from smart_open import open as smart_open
from web3 import Web3
from web3.providers.auto import load_provider_from_uri

from eth_tools.block_iterator import BlockIterator


def uses_web3(f):
    @wraps(f)
    def wrapper(args):
        web3 = create_web3(args["web3_uri"])
        return f(args, web3)
    return wrapper


def create_web3(uri):
    provider = load_provider_from_uri(uri)
    return Web3(provider=provider)


@uses_web3
def fetch_blocks(args, web3):
    """Fetches blocks and stores them in the file given in arguments"""
    block_iterator = BlockIterator(web3, args["start_block"], args["end_block"],
                                   log_interval=args["log_interval"])
    fields = args["fields"]
    with smart_open(args["output"], "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for block in block_iterator:
            row = {field: getattr(block, field) for field in fields}
            writer.writerow(row)
