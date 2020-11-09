import os
from argparse import ArgumentParser

from eth_tools import commands
from eth_tools import constants
from eth_tools.contract_caller import DEFAULT_BLOCK_INTERVAL


def environ_or_required(key):
    default_value = os.environ.get(key)
    if default_value:
        return {"default": default_value}
    return {"required": True}


def add_web3_uri(subparser):
    subparser.add_argument(
        "--web3-uri", help="URI of Web3", **environ_or_required("WEB3_PROVIDER_URI")
    )


def add_etherscan_api_key(subparser):
    subparser.add_argument(
        "--etherscan-api-key",
        help="API key for Etherscan",
        **environ_or_required("ETHERSCAN_API_KEY"),
    )


parser = ArgumentParser(prog="ethereum-tools")

subparsers = parser.add_subparsers(dest="command", help="Command to execute")

fetch_block_timestamps_parser = subparsers.add_parser(
    "fetch-blocks", help="fetches information about given blocks"
)
add_web3_uri(fetch_block_timestamps_parser)
fetch_block_timestamps_parser.add_argument(
    "-f",
    "--fields",
    nargs="+",
    default=constants.DEFAULT_BLOCK_FIELDS,
    help="fields to fetch from the block",
)
fetch_block_timestamps_parser.add_argument(
    "-s",
    "--start-block",
    type=int,
    default=1,
    help="block from which to fetch timestamps",
)
fetch_block_timestamps_parser.add_argument(
    "-e", "--end-block", type=int, help="block up to which to fetch timestamps"
)
fetch_block_timestamps_parser.add_argument(
    "-o", "--output", required=True, help="output file"
)
fetch_block_timestamps_parser.add_argument(
    "--log-interval", type=int, default=1_000, help="interval at which to log"
)

fetch_address_transactions_parser = subparsers.add_parser(
    "fetch-address-transactions",
    help="fetches information about the transactions of a given address from Etherscan",
)
add_etherscan_api_key(fetch_address_transactions_parser)
fetch_address_transactions_parser.add_argument(
    "-a", "--address", required=True, help="address for which to get transactions"
)
fetch_address_transactions_parser.add_argument(
    "--internal",
    default=False,
    action="store_true",
    help="fetch information about internal transactions rather than regular ones",
)
fetch_address_transactions_parser.add_argument(
    "-o", "--output", required=True, help="output file"
)

fetch_transactions_parser = subparsers.add_parser(
    "fetch-transactions",
    help="fetches transactions in given files from an Ethereum node",
)
add_web3_uri(fetch_transactions_parser)
fetch_transactions_parser.add_argument(
    "files", nargs="+", help="files containing transactions to trace"
)
fetch_transactions_parser.add_argument(
    "-r",
    "--include-receipt",
    action="store_true",
    default=False,
    help="include transaction receipt",
)
fetch_transactions_parser.add_argument(
    "-t",
    "--include-traces",
    action="store_true",
    default=False,
    help="include transaction traces",
)
fetch_transactions_parser.add_argument(
    "-o", "--output", required=True, help="output file"
)

call_contract_parser = subparsers.add_parser(
    "call-contract", help="call contract regularly between blocks"
)
add_web3_uri(call_contract_parser)
call_contract_parser.add_argument("address", help="address of the contract")
call_contract_parser.add_argument("--abi", help="path to the contract abi")
call_contract_parser.add_argument("-s", "--start", type=int, help="start block")
call_contract_parser.add_argument("-e", "--end", type=int, help="end block")
call_contract_parser.add_argument(
    "-i",
    "--interval",
    type=int,
    default=DEFAULT_BLOCK_INTERVAL,
    help="interval between calls",
)
call_contract_parser.add_argument(
    "-f", "--func", required=True, help="function to call"
)
call_contract_parser.add_argument(
    "--args", nargs="*", help="arguments to pass to the function"
)
call_contract_parser.add_argument("-o", "--output", help="output file")


fetch_events_parser = subparsers.add_parser(
    "fetch-events", help="Fetches the events from the given contract"
)
add_web3_uri(fetch_events_parser)
fetch_events_parser.add_argument("address", help="Address of the contract")
fetch_events_parser.add_argument("--abi", help="Path to the contract ABI")
fetch_events_parser.add_argument(
    "-s",
    "--start-block",
    help="Start block to fetch the events",
    required=True,
    type=int,
)
fetch_events_parser.add_argument(
    "-e", "--end-block", help="End block to fetch the events", type=int
)
fetch_events_parser.add_argument(
    "-o",
    "--output",
    required=True,
    help="Output jsonl file to store the results (.gz recommended)",
)

bulk_fetch_events_parser = subparsers.add_parser(
    "bulk-fetch-events", help="Fetches the events from the given contracts"
)
add_web3_uri(bulk_fetch_events_parser)
bulk_fetch_events_parser.add_argument(
    "-c", "--config", help="Config file to fetch events"
)
bulk_fetch_events_parser.add_argument("--abis", help="Directory containing ABIs")
bulk_fetch_events_parser.add_argument(
    "-o",
    "--output",
    required=True,
    help="Output directory to store the results",
)


def run():
    args = vars(parser.parse_args())
    if not args["command"]:
        parser.error("no command given")

    func = getattr(commands, args["command"].replace("-", "_"))
    func(args)
