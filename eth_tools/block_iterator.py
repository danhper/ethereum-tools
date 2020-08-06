from web3 import Web3
from web3.types import BlockData

from eth_tools.logger import logger


class Block:
    """Wrapper of web3.types.BlockData prodiving a ``transactions_count`` property
    """
    def __init__(self, data: BlockData):
        self.data = data

    def __getattr__(self, key):
        if key not in self.data:
            raise AttributeError
        value = self.data[key]
        if hasattr(value, "hex"):
            value = value.hex()
        return value

    @property
    def transactions_count(self):
        return len(self.transactions)

    def __repr__(self):
        return "Block(number={number})".format(**self.data)


class BlockIterator:
    """Iterator over Ethereum blocks
    It will lazily fetch each block from ``start_block`` to ``end_block`` inclusive
    using the provided ``web3`` instance.
    """
    def __init__(self, web3: Web3, start_block: int = 0, end_block: int = None,
                 log_interval: int = None):
        self.web3 = web3
        self.start_block = start_block
        if end_block is None:
            end_block = self.web3.eth.blockNumber
        self.end_block = end_block
        self.current_block = self.start_block
        self.log_interval = log_interval

    def __iter__(self):
        logger.info("processing %s blocks", self.blocks_count)
        return self

    @property
    def blocks_count(self):
        return self.end_block - self.start_block + 1

    @property
    def processed_count(self):
        return self.current_block - self.start_block

    def __next__(self) -> Block:
        if self.current_block > self.end_block:
            raise StopIteration
        if self.log_interval and self.processed_count % self.log_interval == 0:
            logger.info("%s/%s", self.processed_count, self.blocks_count)
        block = self.web3.eth.getBlock(self.current_block)
        self.current_block += 1
        return Block(block)
