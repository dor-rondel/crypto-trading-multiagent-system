"""
Analyst for evaluating pool liquidity and slippage risks.
"""

from typing import Any, Dict, List, cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import LiquidityReport
from src.prompts.subagent_prompts import LIQUIDITY_PROMPT_TEMPLATE


class LiquidityAnalyst(BaseAnalyst):
    """
    Evaluates liquidity data to identify execution risks and slippage.
    """

    def __init__(self) -> None:
        super().__init__(output_model=LiquidityReport)

    async def analyze(self, liquidity_data: List[Dict[str, Any]]) -> LiquidityReport:
        """
        Analyzes liquidity data and returns a structured report.
        """
        chain = LIQUIDITY_PROMPT_TEMPLATE | self.structured_llm
        return cast(
            LiquidityReport,
            await chain.ainvoke({"liquidity_data": str(liquidity_data)}),
        )
