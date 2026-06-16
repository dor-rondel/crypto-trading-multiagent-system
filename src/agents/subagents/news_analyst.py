"""
Analyst for evaluating market sentiment from news headlines.
"""

from typing import Any, Dict, List, cast

from src.agents.subagents.base_analyst import BaseAnalyst
from src.models.analysis import NewsReport
from src.prompts.subagent_prompts import NEWS_PROMPT_TEMPLATE


class NewsAnalyst(BaseAnalyst):
    """
    Evaluates recent news to determine macro sentiment.
    """

    def __init__(self) -> None:
        super().__init__(output_model=NewsReport)

    async def analyze(self, headlines: List[Dict[str, Any]]) -> NewsReport:
        """
        Analyzes news headlines and returns a structured report.
        """
        chain = NEWS_PROMPT_TEMPLATE | self.structured_llm
        return cast(NewsReport, await chain.ainvoke({"headlines": str(headlines)}))
