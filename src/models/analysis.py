"""
Definitions for analyst report models.
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class GasReport(BaseModel):
    """
    Report from the Gas Analyst.
    """

    recommendation: str = Field(
        ..., description="Action recommendation based on gas prices"
    )
    rationale: str = Field(..., description="Reasoning for the gas recommendation")
    gas_prices: Dict[str, float] = Field(..., description="Current fees per chain")


class NewsReport(BaseModel):
    """
    Report from the News Analyst.
    """

    sentiment: str = Field(..., description="Overall market sentiment")
    summary: str = Field(..., description="Summary of recent news")
    top_headlines: List[str] = Field(..., description="Relevant news headlines")


class TrendReport(BaseModel):
    """
    Report from the Trend Analyst.
    """

    trends: Dict[str, str] = Field(
        ..., description="Trend for each asset, e.g., 'UPTREND'"
    )
    rationale: str = Field(..., description="Technical analysis reasoning")


class PerformanceReport(BaseModel):
    """
    Report from the Performance Analyst.
    """

    status: str = Field(..., description="Portfolio health status")
    total_unrealized_pnl: float = Field(..., description="Total unrealized PnL in USD")
    asset_breakdown: Dict[str, float] = Field(
        ..., description="PnL breakdown per asset"
    )
    rationale: str = Field(..., description="Risk-based reasoning")


class LiquidityReport(BaseModel):
    """
    Report from the Liquidity Analyst.
    """

    risk_levels: Dict[str, str] = Field(
        ..., description="Liquidity risk level per asset, e.g., {'SOL': 'LOW'}"
    )
    max_recommended_trade_usd: Dict[str, float] = Field(
        ..., description="Max recommended trade size in USD per asset"
    )
    rationale: str = Field(..., description="Reasoning for the liquidity assessment")


class CorrelationReport(BaseModel):
    """
    Report from the Correlation Analyst.
    """

    asset_correlations: Dict[str, float] = Field(
        ..., description="Correlation with BTC for each asset"
    )
    market_regime: str = Field(
        ...,
        description="Identified market regime (e.g., BTC_LED, ALT_SEASON, DECOUPLED)",
    )
    rationale: str = Field(..., description="Reasoning for the correlation analysis")


class WhaleReport(BaseModel):
    """
    Report from the Whale Analyst.
    """

    whale_sentiment: str = Field(
        ..., description="Accumulation vs Distribution sentiment"
    )
    rationale: str = Field(..., description="Reasoning for the whale movement analysis")


class VolatilityReport(BaseModel):
    """
    Report from the Volatility Analyst.
    """

    volatilities: Dict[str, float] = Field(
        ..., description="Realized volatility per asset"
    )
    risk_regime: str = Field(
        ..., description="Risk environment (e.g., CALM, TURBULENT, CRASH_RISK)"
    )
    rationale: str = Field(..., description="Reasoning for the volatility assessment")
