import csv
from functools import wraps

from smart_open import open as smart_open
from web3 import Web3
from web3.providers.auto import load_provider_from_uri

from eth_tools import constants
from eth_tools.block_iterator import BlockIterator
from eth_tools.transaction_fetcher import TransactionsFetcher


def uses_web3(f):
    @wraps(f)
    def wrapper(args):
        web3 = create_web3(args["web3_uri"])
        return f(args, web3)
    return wrapper


def uses_etherscan(f):
    @wraps(f)
    def wrapper(args):
        etherscan_key = args["etherscan_api_key"]
        return f(args, etherscan_key)
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


@uses_etherscan
def fetch_address_transactions(args, etherscan_key):
    fetcher = TransactionsFetcher(etherscan_api_key=etherscan_key)
    internal = args["internal"]
    if internal:
        fields = constants.ETHERSCAN_INTERNAL_TRANSACTION_KEYS
    else:
        fields = constants.ETHERSCAN_TRANSACTION_KEYS
    with smart_open(args["output"], "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for transaction in fetcher.fetch_contract_transactions(args["address"], internal=internal):
            writer.writerow(transaction)
