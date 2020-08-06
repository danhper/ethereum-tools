from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="module")
def web3():
    web3_mock = MagicMock()
    return web3_mock
