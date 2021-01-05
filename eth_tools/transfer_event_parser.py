import os
import json

from collections import defaultdict
from eth_tools.logger import logger


class TransferEventParser:
    """Parses ERC20 'transfer' events"""

    def __init__(self, addresses: dict, start: int = None, end: int = None):
        self.addresses = addresses
        self.balances = defaultdict(lambda: defaultdict(lambda: 0))
        self.key = 'amount'
        self.last_update = defaultdict(lambda: 0)
        self.start = start
        self.end = end

    def parse_events(self, events: list):
        first_event = True
        for event in events:
            if event['event'] == 'Transfer':
                if first_event:
                    self.set_quantity_key(event)
                    self.start = self.start if self.start is not None else event['blockNumber']
                    first_event = False
                self.handle_transfer_event(event)

    def handle_transfer_event(self, event: dict):
        if event['event'] != 'Transfer':
            logger.warning('Failed to parse non-transfer event')
            return
        block = event['blockNumber']
        if event['args']['from'] in self.addresses.values():
            self.updateBalance(event['args']['from'],
                               -1 * event['args'][self.key], block)
        if event['args']['to'] in self.addresses.values():
            self.updateBalance(event['args']['to'],
                               event['args'][self.key], block)

    def updateBalance(self, account: str, change: int, block: int):
        last_updated_block = self.last_update[account]
        self.balances[account][block] = self.balances[account][last_updated_block] + \
            change
        self.last_update[account] = block

    def set_quantity_key(self, event: dict) -> bool:
        """ERC20 contracts don't follow a standard name for the transfer 'amount'.
        This should be handled here."""
        if 'value' in event['args'].keys():
            self.key = 'value'
        elif 'amount' in event['args'].keys():
            self.key = 'amount'
        else:
            logger.error('Key for transfer quantity not found in event parser')
            return False
        return True

    def write_balances(self, token: str, interval: int = None, filepath: str = None):
        for name, address in self.addresses.items():
            fname = token.lower()+"-balances:"+name.lower()+'.csv'
            if filepath is not None:
                fname = filepath + fname
            first_block = True
            last_balance = 0
            inter = 1 if interval is None else interval
            counter = 0
            for block in self.balances[address].keys():
                if first_block:
                    last_block = block
                    first_block = False
                if block == 0:
                    continue
                if block - last_block > 1:
                    # fill in missing blocks
                    block_number = last_block + 1
                    while block_number <= block - 1:
                        counter += 1
                        if counter % inter == 0:
                            self.log_balance(
                                counter, fname, block_number, last_balance)
                        block_number += 1
                if block == last_block + 1:
                    counter += 1
                    if counter % inter == 0:
                        self.log_balance(
                            counter, fname, block, self.balances[address][block])
                last_balance = self.balances[address][block]
                last_block = block

    def log_balance(self, counter: int, fname: str, block_number: int, balance: int):
        if self.start is not None and self.start > block_number:
            return
        if self.end is not None and self.end < block_number:
            return
        logger.info("Blocks: %i", counter)
        with open(fname, 'a+') as f:
            f.write(json.dumps(
                {'blockNumber': block_number, 'balance': balance})+"\n")
