import os
from argparse import ArgumentParser

from eth_tools import commands
from eth_tools import constants



def environ_or_required(key):
    default_value = os.environ.get(key)
    if default_value:
        return {"default": default_value}
    return {"required": True}


def add_web3_uri(subparser):
    subparser.add_argument("--web3-uri", help="URI of Web3",
                           **environ_or_required("WEB3_PROVIDER_URI"))

def add_etherscan_api_key(subparser):
    subparser.add_argument("--etherscan-api-key", help="API key for Etherscan",
                           **environ_or_required("ETHERSCAN_API_KEY"))


parser = ArgumentParser(prog="ethereum-tools")

subparsers = parser.add_subparsers(dest="command", help="Command to execute")

fetch_block_timestamps_parser = subparsers.add_parser(
    "fetch-blocks", help="fetches information about given blocks")
add_web3_uri(fetch_block_timestamps_parser)
fetch_block_timestamps_parser.add_argument(
    "-f", "--fields", nargs="+", default=constants.DEFAULT_BLOCK_FIELDS,
    help="fields to fetch from the block")
fetch_block_timestamps_parser.add_argument(
    "-s", "--start-block", type=int, default=1, help="block from which to fetch timestamps")
fetch_block_timestamps_parser.add_argument(
    "-e", "--end-block", type=int, help="block up to which to fetch timestamps")
fetch_block_timestamps_parser.add_argument(
    "-o", "--output", required=True, help="output file")
fetch_block_timestamps_parser.add_argument(
    "--log-interval", type=int, default=1_000, help="interval at which to log")

fetch_address_transactions_parser = subparsers.add_parser(
    "fetch-address-transactions",
    help="fetches information about the transactions of a given address")
add_etherscan_api_key(fetch_address_transactions_parser)
fetch_address_transactions_parser.add_argument(
    "-a", "--address", required=True, help="address for which to get transactions")
fetch_address_transactions_parser.add_argument(
    "--internal", default=False, action="store_true",
    help="fetch information about internal transactions rather than regular ones")
fetch_address_transactions_parser.add_argument(
    "-o", "--output", required=True, help="output file")


def run():
    args = vars(parser.parse_args())
    if not args["command"]:
        parser.error("no command given")

    func = getattr(commands, args["command"].replace("-", "_"))
    func(args)
