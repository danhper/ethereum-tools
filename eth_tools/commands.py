import csv
import json
import sys
from contextlib import contextmanager
from functools import wraps
from typing import IO, Iterator

from eth_typing import Address
from web3 import Web3
from web3.providers.auto import load_provider_from_uri

from eth_tools import constants
from eth_tools.block_iterator import BlockIterator
from eth_tools.contract_caller import ContractCaller
from eth_tools.event_fetcher import EventFetcher, FetchTask
from eth_tools.json_encoder import EthJSONEncoder
from eth_tools.logger import logger
from eth_tools.transaction_fetcher import TransactionsFetcher
from eth_tools.transaction_tracer import TransactionTracer
from eth_tools.utils import smart_open


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


def create_web3(uri: str):
    provider = load_provider_from_uri(uri, {"timeout": 60})
    return Web3(provider=provider)


@uses_web3
def fetch_blocks(args: dict, web3: Web3):
    """Fetches blocks and stores them in the file given in arguments"""
    block_iterator = BlockIterator(
        web3, args["start_block"], args["end_block"], log_interval=args["log_interval"]
    )
    fields = args["fields"]
    with smart_open(args["output"], "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for block in block_iterator:
            row = {field: getattr(block, field) for field in fields}
            writer.writerow(row)


@uses_etherscan
def fetch_address_transactions(args: dict, etherscan_key: Web3):
    fetcher = TransactionsFetcher(etherscan_api_key=etherscan_key)
    internal = args["internal"]
    if internal:
        fields = constants.ETHERSCAN_INTERNAL_TRANSACTION_KEYS
    else:
        fields = constants.ETHERSCAN_TRANSACTION_KEYS
    with smart_open(args["output"], "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for transaction in fetcher.fetch_contract_transactions(
            args["address"], internal=internal
        ):
            writer.writerow(transaction)


@uses_web3
def fetch_transactions(args: dict, web3: Web3):
    tx_hashes = []
    for filename in args["files"]:
        with smart_open(filename) as fin:
            for tx in csv.DictReader(fin):
                tx_hashes.append(tx["hash"])

    tx_tracer = TransactionTracer(web3)
    done = set()
    with smart_open(args["output"], "w") as fout:
        for i, tx_hash in enumerate(tx_hashes):
            if i % 10 == 0:
                logger.info("progress: %s/%s", i, len(tx_hashes))
            if tx_hash in done:
                continue
            try:
                tx = dict(web3.eth.getTransaction(tx_hash))
                if args["include_receipt"]:
                    tx["receipt"] = web3.eth.getTransactionReceipt(tx_hash)
                if args["include_traces"]:
                    tx["traces"] = tx_tracer.trace_transaction(tx_hash)
                json.dump(tx, fout, cls=EthJSONEncoder)
                print(file=fout)
                done.add(tx_hash)
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning("failed to trace %s: %s", tx_hash, ex)
                continue


@uses_web3
def call_contract(args: dict, web3: Web3):
    with open(args["abi"]) as f:
        abi = json.load(f)
    address: Address = web3.toChecksumAddress(args["address"])
    contract = web3.eth.contract(abi=abi, address=address)
    contract_caller = ContractCaller(contract)
    with smart_open_with_stdout(args["output"], "w") as fout:
        # print(args["args"])
        results = contract_caller.collect_results(
            args["func"],
            start_block=args["start"],
            end_block=args["end"],
            block_interval=args["interval"],
            contract_args=args["args"],
        )
        for block, result in results:
            line = {"block": block, "result": result}
            json.dump(line, fout, cls=EthJSONEncoder)
            print(file=fout)


@uses_web3
def fetch_events(args: dict, web3: Web3):
    fetcher = EventFetcher(web3)
    task = FetchTask.from_dict(args)
    fetcher.fetch_and_persist_events(task, args["output"])


@uses_web3
def bulk_fetch_events(args: dict, web3: Web3):
    fetcher = EventFetcher(web3)
    with smart_open(args["config"]) as f:
        raw_tasks = json.load(f)
    tasks = [FetchTask.from_dict(raw_task, args["abis"]) for raw_task in raw_tasks]
    fetcher.fetch_all_events(tasks, args["output"])


@contextmanager
def smart_open_with_stdout(filename, mode="r", **kwargs) -> Iterator[IO]:
    if filename is None:
        yield sys.stdout
    else:
        with smart_open(filename, mode, **kwargs) as f:
            yield f
