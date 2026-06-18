"""
Tests for TechnicalAnalysis.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.events.market_signal import Candle
from src.tools.technical_analysis import TechnicalAnalysis


@pytest.fixture
def sample_candles():
    """Generates 20 sample candles."""
    candles = []
    base_time = datetime.now(UTC)
    for i in range(20):
        candles.append(
            Candle(
                timestamp=base_time - timedelta(hours=i),
                open=100.0 + i,
                high=105.0 + i,
                low=95.0 + i,
                close=102.0 + i,
                volume=1000.0,
            )
        )
    return candles[::-1]  # Ensure they are in chronological order (oldest -> newest)


def test_technical_analysis_success(sample_candles):
    analyzer = TechnicalAnalysis()
    results = analyzer.calculate_indicators(sample_candles)

    assert "rsi" in results
    assert "macd" in results
    assert "ema" in results
    assert "current_price" in results
    assert results["current_price"] == 102.0


def test_technical_analysis_insufficient_data():
    analyzer = TechnicalAnalysis()
    # Need 14, provide 5
    candles = [
        Candle(
            timestamp=datetime.now(UTC),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
        )
        for _ in range(5)
    ]
    results = analyzer.calculate_indicators(candles)

    assert "error" in results
    assert results["error"] == "Insufficient data for technical analysis"
