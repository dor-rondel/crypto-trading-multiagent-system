"""
Tests for the CoinGecko Provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.market_data.coingecko_provider import CoinGeckoProvider


@pytest.mark.asyncio
async def test_coingecko_provider_success():
    """
    Test successful data fetch from CoinGecko.
    """
    provider = CoinGeckoProvider()
    # Mocking the JSON response from CoinGecko for prices
    # https://api.coingecko.com/api/v3/simple/price
    mock_response = {
        "ethereum": {"usd": 3000.0, "usd_24h_change": -0.5},
        "solana": {"usd": 150.0, "usd_24h_change": 1.2},
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_res = MagicMock()
        mock_res.json.return_value = mock_response
        mock_res.raise_for_status = lambda: None
        mock_get.return_value = mock_res

        snapshot = await provider.get_snapshot(["ETH", "SOL"])

    assert snapshot is not None
    assert snapshot.source == "CoinGecko"
    assert "ETH" in snapshot.assets
    assert "SOL" in snapshot.assets
    assert snapshot.assets["ETH"].price == 3000.0
    assert snapshot.assets["ETH"].change_24h == -0.5
    assert snapshot.assets["SOL"].price == 150.0
    assert snapshot.assets["SOL"].change_24h == 1.2


@pytest.mark.asyncio
async def test_coingecko_provider_failure():
    """
    Test CoinGeckoProvider handling of API failures.
    """
    provider = CoinGeckoProvider()

    with (
        patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_res = MagicMock()
        mock_res.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_res

        # Should raise Exception after retries
        with pytest.raises(Exception, match="API Error"):
            await provider.get_snapshot(["ETH"])

        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2
