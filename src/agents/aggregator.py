"""
Aggregator agent using Groq to generate structured trading plans from analyst reports.
"""

from typing import Dict, Optional, cast

from src.events.market_signal import MarketSnapshot
from src.models.analysis import (
    GasReport,
    LiquidityReport,
    NewsReport,
    PerformanceReport,
    TrendReport,
)
from src.models.trading import TradePlan
from src.prompts.aggregator_prompts import AGGREGATOR_PROMPT_TEMPLATE
from src.utils.llm import get_groq_llm


class AggregatorAgent:
    """
    Aggregator agent that consumes analyst reports to generate a final trade plan.
    """

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.llm = get_groq_llm(model_name=model_name)
        self.structured_llm = self.llm.with_structured_output(TradePlan)

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    async def plan(
        self,
        market_snapshot: MarketSnapshot,
        portfolio_balances: Dict[str, Dict[str, float]],
        gas_report: Optional[GasReport] = None,
        news_report: Optional[NewsReport] = None,
        trend_report: Optional[TrendReport] = None,
        performance_report: Optional[PerformanceReport] = None,
        liquidity_report: Optional[LiquidityReport] = None,
    ) -> TradePlan:
        """
        Generates a trading plan based on aggregated analyst insights.
        """
        balance_str = self._format_balances(portfolio_balances)
        reports_str = self._format_reports(
            gas_report,
            news_report,
            trend_report,
            performance_report,
            liquidity_report,
        )

        chain = AGGREGATOR_PROMPT_TEMPLATE | self.structured_llm
        result = await chain.ainvoke(
            {
                "market_snapshot": market_snapshot.model_dump_json(),
                "portfolio_balances": balance_str,
                "analyst_reports": reports_str,
            }
        )

        if isinstance(result, TradePlan):
            return result

        return cast(TradePlan, result)

    def _format_balances(self, portfolio_balances: Dict[str, Dict[str, float]]) -> str:
        """Formats balances for the prompt."""
        balance_str = ""
        for network, assets in portfolio_balances.items():
            balance_str += f"{network}: {assets}\n"
        return balance_str

    def _format_reports(
        self,
        gas: Optional[GasReport],
        news: Optional[NewsReport],
        trend: Optional[TrendReport],
        perf: Optional[PerformanceReport],
        liquidity: Optional[LiquidityReport],
    ) -> str:
        """Formats analyst reports for the prompt."""
        return (
            f"GAS: {gas.model_dump_json() if gas else 'N/A'}\n"
            f"NEWS: {news.model_dump_json() if news else 'N/A'}\n"
            f"TREND: {trend.model_dump_json() if trend else 'N/A'}\n"
            f"PERF: {perf.model_dump_json() if perf else 'N/A'}\n"
            f"LIQUIDITY: {liquidity.model_dump_json() if liquidity else 'N/A'}\n"
        )
