from unittest.mock import MagicMock, call

import pytest

from eth_tools import transaction_fetcher as tx_fetcher

DUMMY_ADDRESS = "0x" + ("0" * 40)
MAX_CALLS = tx_fetcher.MAX_TRANSACTIONS // tx_fetcher.TRANSACTIONS_PER_PAGE + 1


@pytest.fixture
def fetcher():
    return tx_fetcher.TransactionsFetcher(etherscan_api_key="dummy-api-key")


def make_call(page, internal=False):
    return call(DUMMY_ADDRESS, page, internal=internal)

def make_calls(start_page, end_page, internal=False):
    return [call(DUMMY_ADDRESS, page, internal=internal)
            for page in range(start_page, end_page + 1)]


@pytest.mark.parametrize("responses,calls,txs_count", [
    ([["abc", "def", "ghi"], []], make_calls(1, 2), 3),
    ([["abc", "def", "ghi"], ["jkl"], []], make_calls(1, 3), 4),
    ([["abc"]] * (MAX_CALLS + 1), make_calls(1, 10), 10),
])
def test_fetch_contract_transactions(fetcher, responses, calls, txs_count):
    fetcher._make_transactions_request = MagicMock()
    fetcher._make_transactions_request.side_effect = responses
    result = list(fetcher.fetch_contract_transactions(DUMMY_ADDRESS))
    fetcher._make_transactions_request.assert_has_calls(calls)
    assert len(result) == txs_count
