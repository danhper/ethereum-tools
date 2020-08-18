from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from web3.contract import Contract

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
        total_count = end_block - start_block + 1
        def run_task(block):
            return self.call_func(func_name, block, *args, **kwargs)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            blocks = range(start_block, end_block + 1, block_interval)
            results = executor.map(run_task, blocks)
            for i, (block, result) in enumerate(zip(blocks, results)):
                if i % 10 == 0:
                    logger.info("progress: %s/%s", i, total_count)
                yield (block, result)

    def call_func(self, func_name, block, *args, **kwargs):
        func = getattr(self.contract.functions, func_name)
        return func(*args, **kwargs).call(block_identifier=block)
