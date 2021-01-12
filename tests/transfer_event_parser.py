import pytest
import json
import sys
import os

from eth_tools.transfer_event_parser import TransferEventParser

mock_event = {"args": {"from": "0xA8502b841D9fcD5d2a4C7439A13e87796AEd56A1", "to": "0x0001FB050Fe7312791bF6475b96569D83F695C9f", "value": 174003773318124380}, "event": "Transfer", "logIndex": 44, "transactionIndex": 40,
              "transactionHash": "0x69dd5baf185d9c4349d70a84963885ed301614d3c8d0457955d4df06e8bcbcb8", "address": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e", "blockHash": "0x858a94be7abaa2aa124a3aef22bd4355afd460164b63b400ea12af7a3128e90f", "blockNumber": 10478438}


@pytest.fixture
def addresses():
    fname = os.path.join(os.path.dirname(__file__),
                         'test_data/dummyAddresses.json')
    with open(fname) as f:
        addresses = json.load(f)
    return addresses


@pytest.fixture
def events():
    fname = os.path.join(os.path.dirname(__file__),
                         'test_data/dummyEvents.json')
    with open(fname) as f:
        events = [json.loads(e) for e in f]
    return events


@pytest.fixture
def dummy_balances():
    return {"0x123": {2: 10, 3: 11, 5: 18}}


@pytest.fixture
def dummy_addresses():
    return {"addr": "0x123"}


def test_handle_transfer_event(addresses):
    transfer_event_parser = TransferEventParser(addresses)
    transfer_event_parser.set_keys(mock_event)
    transfer_event_parser.handle_transfer_event(mock_event)
    assert transfer_event_parser.balances["0x0001FB050Fe7312791bF6475b96569D83F695C9f"][10478438] == 174003773318124380


def test_execute_events(addresses, events):
    transfer_event_parser = TransferEventParser(addresses)
    transfer_event_parser.execute_events(events)
    assert transfer_event_parser.balances[
        "0x0001FB050Fe7312791bF6475b96569D83F695C9f"][10478649] == 9995796750644777900207
    assert transfer_event_parser.balances["0x28b88cfD875C883cDb61938C97B8d1baabf31c88"][10478826] == 90896908769421890


def test_write_balances(dummy_addresses, dummy_balances, tmp_path):
    transfer_event_parser = TransferEventParser(dummy_addresses)
    transfer_event_parser.balances = dummy_balances
    transfer_event_parser.start = 2
    transfer_event_parser.write_balances("tok", filepath=str(tmp_path) + "/")
    output_path = tmp_path / "tok-balances:addr.csv"
    assert os.path.exists(output_path)
    with open(output_path) as f:
        print(f.read())
    with open(output_path) as f:
        balances = [json.loads(line) for line in f]
    assert balances == [{"blockNumber": 2, "balance": 10}, {"blockNumber": 3, "balance": 11}, {
        "blockNumber": 4, "balance": 11}, {"blockNumber": 5, "balance": 18}]
