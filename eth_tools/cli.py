import os
from argparse import ArgumentParser

from eth_tools import commands
from eth_tools import constants



def environ_or_required(key):
    default_value = os.environ.get(key)
    if default_value:
        return {"default": default_value}
    return {"required": True}


parser = ArgumentParser(prog="ethereum-tools")
parser.add_argument("--web3-uri", help="URI of Web3",
                    **environ_or_required("WEB3_PROVIDER_URI"))

subparsers = parser.add_subparsers(dest="command", help="Command to execute")

fetch_block_timestamps_parser = subparsers.add_parser(
    "fetch-blocks", help="fetches information about given blocks")
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


def run():
    args = vars(parser.parse_args())
    if not args["command"]:
        parser.error("no command given")

    func = getattr(commands, args["command"].replace("-", "_"))
    func(args)
