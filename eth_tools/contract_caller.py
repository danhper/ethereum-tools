from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from web3.contract import Contract

DEFAULT_BLOCK_INTERVAL = 1_000


class ContractCaller:
    def __init__(self, contract: Contract):
        self.contract = contract

    def collect_results(self, func_name, start_block, end_block, *args, block_interval=DEFAULT_BLOCK_INTERVAL, **kwargs):
        max_workers = multiprocessing.cpu_count() * 5
        def run_task(block):
            return self.call_func(func_name, block, *args, **kwargs)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            blocks = range(start_block, end_block, block_interval)
            results = executor.map(run_task, blocks)
            for block, result in zip(blocks, results):
                yield (block, result)

    def call_func(self, func_name, block, *args, **kwargs):
        func = getattr(self.contract.functions, func_name)
        return func(*args, **kwargs).call(block)
