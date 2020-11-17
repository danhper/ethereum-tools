from argparse import RawTextHelpFormatter
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from os import path
from typing import Iterable, Iterator, List, Optional

from eth_typing import Address
from web3 import Web3
from web3.contract import Contract
from web3.types import FilterParams, LogReceipt

from eth_tools.json_encoder import EthJSONEncoder
from eth_tools.logger import logger
from eth_tools.utils import smart_open


@dataclass(repr=False)
class FetchTask:
    address: str
    abi: dict
    start_block: int
    end_block: Optional[int] = None
    name: Optional[str] = None

    @property
    def checksum_address(self) -> Address:
        return Web3.toChecksumAddress(self.address)

    def __repr__(self) -> str:
        return (
            f"FetchTask(address='{self.address}', "
            f"start_block={self.start_block}, end_block={self.end_block})"
        )

    @property
    def display_name(self):
        if self.name:
            return self.name
        return self.address

    @classmethod
    def from_dict(cls, raw_task: dict, abi_paths: str = None):
        raw_task = raw_task.copy()
        default_abi_name = raw_task.get("name", raw_task["address"]).lower()
        abi_path = raw_task.pop("abi", default_abi_name + ".json")
        if abi_paths:
            abi_path = path.join(abi_paths, abi_path)
        with smart_open(abi_path) as f:
            raw_task["abi"] = json.load(f)
        keys = ["address", "abi", "start_block", "end_block", "name"]
        return cls(**{k: raw_task.get(k) for k in keys})


class ContractFetcher:
    BLOCK_GRANULARITIES = [10_000, 1_000, 100, 10, 1]

    def __init__(self, contract: Contract):
        self.contract = contract
        contract_events = [event() for event in self.contract.events]  # type: ignore
        self.events_by_topic = {
            event.build_filter().topics[0]: event
            for event in contract_events
            if not event.abi["anonymous"]
        }

    def process_log(self, event: LogReceipt) -> LogReceipt:
        topics = event.get("topics")
        if topics and topics[0].hex() in self.events_by_topic:
            event = self.events_by_topic[topics[0].hex()].processLog(event)
        return event

    def process_logs(self, events: List[LogReceipt]) -> List[LogReceipt]:
        return [self.process_log(event) for event in events]

    def _fetch_events(self, start_block: int, end_block: int) -> Iterable[LogReceipt]:
        event_filter = self.contract.web3.eth.filter(
            FilterParams(
                address=self.contract.address, fromBlock=start_block, toBlock=end_block
            )
        )
        events = event_filter.get_all_entries()
        return self.process_logs(events)

    def _fetch_batch_parallel(
        self, start_blocks: List[int], end_blocks: List[int]
    ) -> Iterable[LogReceipt]:
        if len(start_blocks) == 1:
            return self._fetch_events(start_blocks[0], end_blocks[0])
        result = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            for events in executor.map(self._fetch_events, start_blocks, end_blocks):
                result.extend(events)
        return result

    def _fetch_batch(self, start_block: int, end_block: int) -> Iterable[LogReceipt]:
        for granularity in self.BLOCK_GRANULARITIES:
            block_count = end_block - start_block + 1
            iterations = range(math.ceil(block_count / granularity))
            start_blocks = [(start_block + i * granularity) for i in iterations]
            end_blocks = [min(b + granularity - 1, end_block) for b in start_blocks]
            try:
                return self._fetch_batch_parallel(start_blocks, end_blocks)
            except Exception:  # pylint: disable=broad-except
                pass
        raise ValueError(
            f"unable to fetch events for {self.contract.address} "
            f"from block {start_block} to {end_block}"
        )

    def fetch_events(
        self, start_block: int, end_block: int = None
    ) -> Iterator[LogReceipt]:
        if end_block is None:
            end_block = self.contract.web3.eth.blockNumber

        block_count = end_block - start_block + 1
        granularity = self.BLOCK_GRANULARITIES[0]

        for i in range(math.ceil(block_count / granularity)):
            logger.info(
                "%s progress: %s/%s",
                self.contract.address,
                i * granularity,
                block_count,
            )
            batch_start_block = start_block + i * granularity
            batch_end_block = min(batch_start_block + granularity - 1, end_block)
            yield from self._fetch_batch(batch_start_block, batch_end_block)


class EventFetcher:
    def __init__(self, web3: Web3):
        self.web3 = web3

    def fetch_events(self, task: FetchTask) -> Iterator[LogReceipt]:
        contract = self.web3.eth.contract(address=task.checksum_address, abi=task.abi)
        fetcher = ContractFetcher(contract)
        return fetcher.fetch_events(task.start_block, task.end_block)

    def fetch_and_persist_events(self, task: FetchTask, output_file: str):
        with smart_open(output_file, "w") as f:
            for event in self.fetch_events(task):
                print(json.dumps(event, cls=EthJSONEncoder), file=f)

    def fetch_all_events(self, fetch_tasks: List[FetchTask], output_directory: str):
        with ThreadPoolExecutor() as executor:
            filepaths = [
                path.join(output_directory, task.display_name) + ".jsonl.gz"
                for task in fetch_tasks
            ]
            futures = {
                executor.submit(self.fetch_and_persist_events, task, output): task
                for task, output in zip(fetch_tasks, filepaths)
            }
            for future in as_completed(futures):
                task = futures[future]
                ex = future.exception()
                if ex:
                    logger.error(
                        "failed to process %s (%s): %s", task.name, task.address, ex
                    )
                else:
                    logger.info("completed to process %s (%s)", task.name, task.address)
