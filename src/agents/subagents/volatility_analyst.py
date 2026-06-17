"""
Analyst for evaluating market volatility and risk regimes.
"""

from typing import Any, Dict, List, cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import VolatilityReport
from src.prompts.subagent_prompts import VOLATILITY_PROMPT_TEMPLATE


class VolatilityAnalyst(BaseAnalyst):
    """
    Evaluates price variance and risk regimes.
    """

    def __init__(self) -> None:
        super().__init__(output_model=VolatilityReport)

    async def analyze(self, volatility_data: List[Dict[str, Any]]) -> VolatilityReport:
        """
        Analyzes volatility data and returns a structured report.
        """
        chain = VOLATILITY_PROMPT_TEMPLATE | self.structured_llm
        return cast(
            VolatilityReport,
            await chain.ainvoke({"volatility_data": str(volatility_data)}),
        )
