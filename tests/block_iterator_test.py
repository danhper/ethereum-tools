from unittest.mock import PropertyMock, MagicMock, call

import pytest
from web3.types import BlockData

from eth_tools.block_iterator import BlockIterator


def test_initialization(web3):
    type(web3.eth).blockNumber = PropertyMock(return_value=100)
    block_iterator = BlockIterator(web3)
    assert block_iterator.start_block == 0
    assert block_iterator.end_block == 100
    assert block_iterator.current_block == 0
    assert block_iterator.blocks_count == 101
    assert block_iterator.processed_count == 0


def test_next(web3):
    first_block = MagicMock(spec=BlockData)
    second_block = MagicMock(spec=BlockData)
    web3.eth.getBlock.side_effect = [first_block, second_block]
    block_iterator = BlockIterator(web3, start_block=0, end_block=1)

    block = next(block_iterator)
    assert block.data == first_block
    block = next(block_iterator)
    assert block.data == second_block
    with pytest.raises(StopIteration):
        next(block_iterator)
    assert block_iterator.processed_count == 2

    web3.eth.getBlock.assert_has_calls([call(0), call(1)])
