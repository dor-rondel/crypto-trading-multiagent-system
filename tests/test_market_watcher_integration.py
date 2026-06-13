from unittest.mock import AsyncMock, MagicMock

import pytest

from src.events.market_signal import AssetPrice, MarketSnapshot
from src.services.market_watcher import MarketWatcher


@pytest.mark.asyncio
async def test_market_watcher_aggregation():
    # Mock providers
    mock_provider1 = MagicMock()
    mock_provider1.get_snapshot = AsyncMock(
        return_value=MarketSnapshot(
            source="provider1", assets={"SOL": AssetPrice(price=100.0)}
        )
    )

    mock_provider2 = MagicMock()
    mock_provider2.get_snapshot = AsyncMock(
        return_value=MarketSnapshot(
            source="provider2", assets={"ETH": AssetPrice(price=2000.0)}
        )
    )

    watcher = MarketWatcher(
        assets=["SOL", "ETH"], interval=0.1, providers=[mock_provider1, mock_provider2]
    )

    # Callback to verify aggregation
    captured_snapshot = None

    async def callback(snapshot):
        nonlocal captured_snapshot
        captured_snapshot = snapshot
        watcher.stop()  # Stop loop

    watcher.on_snapshot(callback)

    # Run loop
    await watcher.start()

    # Assertions
    assert captured_snapshot is not None
    assert "SOL" in captured_snapshot.assets
    assert "ETH" in captured_snapshot.assets
    assert captured_snapshot.source == "provider1, provider2"
