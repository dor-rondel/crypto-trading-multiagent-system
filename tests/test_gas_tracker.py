"""
Tests for the Gas Tracker.
"""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.tools.gas_tracker import GasTracker


@pytest.mark.asyncio
async def test_gas_tracker_success():
    """
    Test successful gas price fetching for all chains.
    """
    with (
        patch("src.tools.gas_tracker.SolanaClient"),
        patch("src.tools.gas_tracker.Web3"),
        patch("src.tools.gas_tracker.Web3.from_wei", return_value=1.0),
    ):
        # Configure mock Web3 instance for Eth and Avax
        mock_eth_w3 = MagicMock()
        type(mock_eth_w3.eth).gas_price = PropertyMock(return_value=1000000000)

        mock_avax_w3 = MagicMock()
        type(mock_avax_w3.eth).gas_price = PropertyMock(return_value=25000000000)

        tracker = GasTracker()

        # Override the providers with our mocks
        tracker.eth_w3 = mock_eth_w3
        tracker.avax_w3 = mock_avax_w3

        prices = await tracker.get_all_gas_prices()

    assert "sepolia" in prices
    assert prices["sepolia"]["gas_price_gwei"] == 1.0
    assert "avalanche-fuji" in prices
    assert (
        prices["avalanche-fuji"]["gas_price_gwei"] == 1.0
    )  # Will be 1.0 because of the mock
    assert "solana" in prices
    assert prices["solana"]["standard_fee_lamports"] == 5000


@pytest.mark.asyncio
async def test_gas_tracker_failure():
    """
    Test GasTracker handling of RPC failures.
    """
    with (
        patch("src.tools.gas_tracker.SolanaClient"),
        patch("src.tools.gas_tracker.Web3"),
    ):
        tracker = GasTracker()

        # Configure mocks to fail
        tracker.eth_w3 = MagicMock()
        type(tracker.eth_w3.eth).gas_price = PropertyMock(
            side_effect=Exception("RPC Error")
        )

        tracker.avax_w3 = MagicMock()
        type(tracker.avax_w3.eth).gas_price = PropertyMock(
            side_effect=Exception("RPC Error")
        )

        prices = await tracker.get_all_gas_prices()

    assert "error" in prices["sepolia"]
    assert "error" in prices["avalanche-fuji"]
    assert "solana" in prices
