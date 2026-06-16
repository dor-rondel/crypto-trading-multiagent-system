"""
Definitions for analyst report models.
"""

from typing import List

from pydantic import BaseModel, Field


class GasReport(BaseModel):
    """
    Report from the Gas Analyst.
    """

    recommendation: str = Field(
        ..., description="Action recommendation based on gas prices"
    )
    rationale: str = Field(..., description="Reasoning for the gas recommendation")
    gas_prices: dict = Field(..., description="Current fees across chains")


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

    trends: dict = Field(..., description="Identified trends for each asset")
    rationale: str = Field(..., description="Technical analysis reasoning")


class PerformanceReport(BaseModel):
    """
    Report from the Performance Analyst.
    """

    status: str = Field(..., description="Portfolio health status")
    total_unrealized_pnl: float = Field(..., description="Total unrealized PnL in USD")
    asset_breakdown: dict = Field(..., description="PnL breakdown per asset")
    rationale: str = Field(..., description="Risk-based reasoning")
