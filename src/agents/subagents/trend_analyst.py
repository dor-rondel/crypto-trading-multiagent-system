"""
Analyst for evaluating technical trends from market history.
"""

from typing import cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import TrendReport
from src.prompts.subagent_prompts import TREND_PROMPT_TEMPLATE


class TrendAnalyst(BaseAnalyst):
    """
    Evaluates OHLCV data to identify short-term trends.
    """

    def __init__(self) -> None:
        super().__init__(output_model=TrendReport)

    async def analyze(self, market_history: str) -> TrendReport:
        """
        Analyzes market history and returns a structured report.
        """
        chain = TREND_PROMPT_TEMPLATE | self.structured_llm
        return cast(
            TrendReport, await chain.ainvoke({"market_history": market_history})
        )
