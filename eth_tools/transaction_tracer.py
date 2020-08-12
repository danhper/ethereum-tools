from web3 import Web3
from retry import retry

from eth_tools.logger import logger


class TransactionTracer:
    def __init__(self, web3: Web3):
        self.web3 = web3

    @retry(delay=1, backoff=2, tries=3, logger=logger)
    def trace_transaction(self, tx_hash: str, disable_memory=True, disable_storage=True):
        params = [tx_hash, {"disableMemory": disable_memory, "disableStorage": disable_storage}]
        return self.web3.manager.request_blocking("debug_traceTransaction", params=params)
