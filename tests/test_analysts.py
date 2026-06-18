"""
Unit tests for all specialized analyst subagents.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.subagents.correlation_analyst import CorrelationAnalyst
from src.agents.subagents.gas_analyst import GasAnalyst
from src.agents.subagents.liquidity_analyst import LiquidityAnalyst
from src.agents.subagents.news_analyst import NewsAnalyst
from src.agents.subagents.performance_analyst import PerformanceAnalyst
from src.agents.subagents.trend_analyst import TrendAnalyst
from src.agents.subagents.volatility_analyst import VolatilityAnalyst
from src.agents.subagents.whale_analyst import WhaleAnalyst
from src.models.analysis import (
    CorrelationReport,
    GasReport,
    LiquidityReport,
    NewsReport,
    PerformanceReport,
    TrendReport,
    VolatilityReport,
    WhaleReport,
)


@pytest.mark.asyncio
async def test_gas_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = GasAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = GasReport(
                recommendation="PROCEED", rationale="Low fees", gas_prices={"ETH": 2.0}
            )
            report = await analyst.analyze({"ETH": 2.0})
            assert isinstance(report, GasReport)
            assert report.recommendation == "PROCEED"


@pytest.mark.asyncio
async def test_news_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = NewsAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = NewsReport(
                sentiment="BULLISH",
                summary="Good news",
                top_headlines=["Headline 1"],
            )
            report = await analyst.analyze([{"title": "Headline 1"}])
            assert isinstance(report, NewsReport)
            assert report.sentiment == "BULLISH"


@pytest.mark.asyncio
async def test_trend_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = TrendAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = TrendReport(
                trends={"SOL": "UPTREND"}, rationale="Bullish trend"
            )
            report = await analyst.analyze("market history data")
            assert isinstance(report, TrendReport)
            assert report.trends["SOL"] == "UPTREND"


@pytest.mark.asyncio
async def test_performance_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = PerformanceAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = PerformanceReport(
                status="HEALTHY",
                total_unrealized_pnl=100.0,
                asset_breakdown={"SOL": 100.0},
                rationale="Risk low",
            )
            report = await analyst.analyze("position data")
            assert isinstance(report, PerformanceReport)
            assert report.status == "HEALTHY"


@pytest.mark.asyncio
async def test_liquidity_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = LiquidityAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = LiquidityReport(
                risk_levels={"SOL": "LOW"},
                max_recommended_trade_usd={"SOL": 5000.0},
                rationale="High depth",
            )
            report = await analyst.analyze([{"asset": "SOL"}])
            assert isinstance(report, LiquidityReport)
            assert report.risk_levels["SOL"] == "LOW"


@pytest.mark.asyncio
async def test_correlation_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = CorrelationAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = CorrelationReport(
                asset_correlations={"SOL": 0.5},
                market_regime="BTC_LED",
                rationale="High correlation",
            )
            report = await analyst.analyze([{"asset": "SOL"}])
            assert isinstance(report, CorrelationReport)
            assert report.market_regime == "BTC_LED"


@pytest.mark.asyncio
async def test_whale_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = WhaleAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = WhaleReport(
                whale_sentiment="accumulation", rationale="Whales buying"
            )
            report = await analyst.analyze([{"asset": "SOL"}])
            assert isinstance(report, WhaleReport)
            assert report.whale_sentiment == "accumulation"


@pytest.mark.asyncio
async def test_volatility_analyst():
    with patch("src.agents.subagents.base_analyst.get_groq_llm"):
        analyst = VolatilityAnalyst()
        with patch.object(analyst, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = VolatilityReport(
                volatilities={"SOL": 0.5},
                risk_regime="CALM",
                rationale="Low volatility",
            )
            report = await analyst.analyze([{"asset": "SOL"}])
            assert isinstance(report, VolatilityReport)
            assert report.risk_regime == "CALM"
