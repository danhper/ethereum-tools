# eth-tools

Small library/CLI tool wrapping web3py.

## Installation

```
pip install ethereum-tools
```

## CLI Usage

Web3 provider needs to be set either through the `WEB3_PROVIDER_URI` environment
variable or through the `--web3-uri` CLI flag.

### Fetching blocks

```
eth-tools fetch-blocks -s 10000000 -e 10000999 -o blocks.csv.gz
```

### Fetching events

```
eth-tools fetch-events 0x6b175474e89094c44da98b954eedeac495271d0f --abi /path/to/abi.json -s 10000000 -e 10000999 -o events.jsonl.gz
```

## Library usage

```python
from web3 import Web3
from web3.providers.auto import load_provider_from_environment

from eth_tools.block_iterator import BlockIterator


provider = load_provider_from_environment()
web3 = Web3(provider)
block_iterator = BlockIterator(web3, start_block=10_000_000, end_block=10_000_999)

for block in block_iterator:
    print(block.number)
```
