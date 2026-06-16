"""
Analyst for evaluating portfolio risk and current PnL performance.
"""

from typing import cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import PerformanceReport
from src.prompts.subagent_prompts import PERFORMANCE_PROMPT_TEMPLATE


class PerformanceAnalyst(BaseAnalyst):
    """
    Evaluates current positions and PnL to identify risk levels.
    """

    def __init__(self) -> None:
        super().__init__(output_model=PerformanceReport)

    async def analyze(self, positions_context: str) -> PerformanceReport:
        """
        Analyzes positions and returns a structured report.
        """
        chain = PERFORMANCE_PROMPT_TEMPLATE | self.structured_llm
        return cast(
            PerformanceReport, await chain.ainvoke({"positions": positions_context})
        )
