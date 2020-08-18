from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from web3.contract import Contract
from retry import retry

from eth_tools.logger import logger

DEFAULT_BLOCK_INTERVAL = 1_000


class ContractCaller:
    def __init__(self, contract: Contract):
        self.contract = contract

    def collect_results(self, func_name, start_block, *args,
                        end_block=None, block_interval=DEFAULT_BLOCK_INTERVAL, **kwargs):
        max_workers = multiprocessing.cpu_count() * 5
        if end_block is None:
            end_block = self.contract.web3.eth.blockNumber

        def run_task(block):
            try:
                return self.call_func(func_name, block, *args, **kwargs)
            except Exception as ex: # pylint: disable=broad-except
                logger.error("failed to fetch block %s: %s", block, ex)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            blocks = range(start_block, end_block + 1, block_interval)
            total_count = len(blocks)
            results = executor.map(run_task, blocks)
            for i, (block, result) in enumerate(zip(blocks, results)):
                if i % 10 == 0:
                    logger.info("progress: %s/%s (%.2f%%)", i, total_count, i / total_count * 100)
                if result:
                    yield (block, result)

    @retry(delay=1, backoff=2, tries=3, logger=logger)
    def call_func(self, func_name, block, *args, **kwargs):
        func = getattr(self.contract.functions, func_name)
        return func(*args, **kwargs).call(block_identifier=block)
