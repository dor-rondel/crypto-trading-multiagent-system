import pytest

from src.tools.liquidity_provider import LiquidityProvider


@pytest.mark.asyncio
async def test_liquidity_provider_logic():
    provider = LiquidityProvider()
    assets = ["ETH", "SOL"]
    data = await provider.get_liquidity_metrics(assets)

    assert len(data) == 2

    # Check specific logic for ETH/SOL
    for item in data:
        if item["asset"] == "ETH":
            assert item["pool_depth_usd"] == 5000000
            assert item["spread_bps"] == 5
        if item["asset"] == "SOL":
            assert item["pool_depth_usd"] == 1200000
            assert item["spread_bps"] == 12
