"""
Analyst for evaluating market correlations with BTC.
"""

from typing import Any, Dict, List, cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import CorrelationReport
from src.prompts.subagent_prompts import CORRELATION_PROMPT_TEMPLATE


class CorrelationAnalyst(BaseAnalyst):
    """
    Evaluates correlation data to identify market regimes and decoupling.
    """

    def __init__(self) -> None:
        super().__init__(output_model=CorrelationReport)

    async def analyze(
        self, correlation_data: List[Dict[str, Any]]
    ) -> CorrelationReport:
        """
        Analyzes correlation data and returns a structured report.
        """
        chain = CORRELATION_PROMPT_TEMPLATE | self.structured_llm
        return cast(
            CorrelationReport,
            await chain.ainvoke({"correlation_data": str(correlation_data)}),
        )
