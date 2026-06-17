"""
Binance implementation of the market data provider.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

import httpx

from src.events.market_signal import AssetPrice, Candle, MarketSnapshot
from src.tools.market_data.base_provider import BaseMarketProvider
from src.utils.retry import retry_async

logger = logging.getLogger(__name__)


class BinanceProvider(BaseMarketProvider):
    """
    Fetches market data from the Binance Public API.
    """

    BASE_URL = "https://api.binance.com/api/v3"

    # Map internal symbols to Binance symbols
    SYMBOL_MAP = {
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT",
        "AVAX": "AVAXUSDT",
    }

    @retry_async(retries=3, delay=1.0, backoff=2.0)
    async def get_snapshot(self, assets: List[str]) -> Optional[MarketSnapshot]:
        """
        Fetches current prices and history from Binance and returns a MarketSnapshot.
        """
        binance_symbols = [
            self.SYMBOL_MAP[a.upper()] for a in assets if a.upper() in self.SYMBOL_MAP
        ]

        if not binance_symbols:
            logger.warning("No valid Binance symbols found for assets: %s", assets)
            return None

        async with httpx.AsyncClient(timeout=15.0) as client:
            ticker_data = await self._fetch_ticker_data(client, binance_symbols)
            history_data = await self._fetch_history_data(client, binance_symbols)

        asset_prices = self._parse_snapshot_data(ticker_data, history_data)

        if not asset_prices:
            return None

        return MarketSnapshot(assets=asset_prices, source="Binance")

    async def _fetch_ticker_data(
        self, client: httpx.AsyncClient, symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetches current prices and 24h change."""
        symbols_param = '["' + '","'.join(symbols) + '"]'
        ticker_url = f"{self.BASE_URL}/ticker/24hr"
        response = await client.get(ticker_url, params={"symbols": symbols_param})
        response.raise_for_status()
        return response.json()  # type: ignore

    async def _fetch_history_data(
        self, client: httpx.AsyncClient, symbols: List[str]
    ) -> Dict[str, List[Any]]:
        """Fetches last 24h of hourly OHLCV data."""
        history_data = {}
        for symbol in symbols:
            kline_url = f"{self.BASE_URL}/klines"
            params: Dict[str, Any] = {"symbol": symbol, "interval": "1h", "limit": 24}
            k_resp = await client.get(kline_url, params=params)
            if k_resp.status_code == 200:
                history_data[symbol] = k_resp.json()
        return history_data

    def _parse_snapshot_data(
        self, ticker_data: List[Dict[str, Any]], history_data: Dict[str, List[Any]]
    ) -> Dict[str, AssetPrice]:
        """Combines ticker and history data into AssetPrice models."""
        asset_prices: Dict[str, AssetPrice] = {}
        id_to_symbol = {v: k for k, v in self.SYMBOL_MAP.items()}
        ticker_map = {t["symbol"]: t for t in ticker_data}

        for binance_symbol, ticker in ticker_map.items():
            symbol = id_to_symbol.get(binance_symbol)
            if not symbol:
                continue

            candles = []
            if binance_symbol in history_data:
                for k in history_data[binance_symbol]:
                    candles.append(
                        Candle(
                            timestamp=datetime.fromtimestamp(k[0] / 1000, tz=UTC),
                            open=float(k[1]),
                            high=float(k[2]),
                            low=float(k[3]),
                            close=float(k[4]),
                            volume=float(k[5]),
                        )
                    )

            asset_prices[symbol] = AssetPrice(
                price=float(ticker["lastPrice"]),
                change_24h=float(ticker["priceChangePercent"]),
                history=candles if candles else None,
            )

        return asset_prices
