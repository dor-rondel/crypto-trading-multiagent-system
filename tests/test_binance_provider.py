"""
Tests for the Binance Provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.market_data.binance_provider import BinanceProvider


@pytest.mark.asyncio
async def test_binance_provider_success():
    """
    Test successful data fetch from Binance.
    """
    provider = BinanceProvider()
    mock_ticker_response = [
        {"symbol": "ETHUSDT", "lastPrice": "3000.0", "priceChangePercent": "-0.5"}
    ]
    mock_history_response = [
        [1700000000000, "2900.0", "3100.0", "2800.0", "3000.0", "100.0"]
    ]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_res1 = MagicMock()
        mock_res1.json.return_value = mock_ticker_response
        mock_res1.raise_for_status = lambda: None

        mock_res2 = MagicMock()
        mock_res2.json.return_value = mock_history_response
        mock_res2.raise_for_status = lambda: None

        mock_get.side_effect = [mock_res1, mock_res2]

        snapshot = await provider.get_snapshot(["ETH"])

    assert snapshot is not None
    assert snapshot.source == "Binance"
    assert "ETH" in snapshot.assets
    assert snapshot.assets["ETH"].price == 3000.0
    assert snapshot.assets["ETH"].change_24h == -0.5


@pytest.mark.asyncio
async def test_binance_provider_failure():
    """
    Test BinanceProvider handling of API failures.
    """
    provider = BinanceProvider()

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
