"""
Analyst for evaluating on-chain whale movements.
"""

from typing import Any, Dict, List, cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import WhaleReport
from src.prompts.subagent_prompts import WHALE_PROMPT_TEMPLATE


class WhaleAnalyst(BaseAnalyst):
    """
    Evaluates large on-chain transactions and smart money flows.
    """

    def __init__(self) -> None:
        super().__init__(output_model=WhaleReport)

    async def analyze(self, whale_data: List[Dict[str, Any]]) -> WhaleReport:
        """
        Analyzes whale data and returns a structured report.
        """
        chain = WHALE_PROMPT_TEMPLATE | self.structured_llm
        return cast(WhaleReport, await chain.ainvoke({"whale_data": str(whale_data)}))
