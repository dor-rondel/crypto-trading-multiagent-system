import pytest

from src.tools.correlation_provider import CorrelationProvider


@pytest.mark.asyncio
async def test_correlation_provider_logic():
    provider = CorrelationProvider()
    assets = ["ETH", "SOL", "BTC"]
    data = await provider.get_correlation_data(assets)

    # Check that BTC is excluded (it's not in the returned list)
    asset_symbols = [d["asset"] for d in data]
    assert "BTC" not in asset_symbols
    assert "ETH" in asset_symbols
    assert "SOL" in asset_symbols

    # Check specific logic for ETH/SOL
    for item in data:
        if item["asset"] == "ETH":
            assert item["vs_btc_7d"] == 0.85
        if item["asset"] == "SOL":
            assert item["trend"] == "increasing"
