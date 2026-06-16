"""
Analyst for evaluating network fees and transaction urgency.
"""

from typing import cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import GasReport
from src.prompts.subagent_prompts import GAS_PROMPT_TEMPLATE


class GasAnalyst(BaseAnalyst):
    """
    Evaluates multi-chain gas prices to recommend execution timing.
    """

    def __init__(self) -> None:
        super().__init__(output_model=GasReport)

    async def analyze(self, gas_prices: dict) -> GasReport:
        """
        Analyzes gas prices and returns a structured report.
        """
        chain = GAS_PROMPT_TEMPLATE | self.structured_llm
        return cast(GasReport, await chain.ainvoke({"gas_prices": str(gas_prices)}))
