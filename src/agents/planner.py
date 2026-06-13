"""
Planner agent using Groq to generate structured trading plans.
"""

import os
from typing import Dict, cast

from langchain_groq import ChatGroq
from pydantic import SecretStr

from src.events.market_signal import MarketSnapshot
from src.models.trading import TradePlan
from src.prompts.planner_prompts import PLANNER_PROMPT_TEMPLATE


class PlannerAgent:
    """
    Planner agent that uses an LLM to generate trading plans.
    """

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.llm = ChatGroq(
            model=model_name,
            api_key=SecretStr(api_key),
            temperature=0.1,
        )
        self.structured_llm = self.llm.with_structured_output(TradePlan)

    async def plan(
        self,
        market_snapshot: MarketSnapshot,
        portfolio_balances: Dict[str, Dict[str, float]],
    ) -> TradePlan:
        """
        Generates a trading plan based on market data and current balances.
        """
        chain = PLANNER_PROMPT_TEMPLATE | self.structured_llm

        # Format balances for the prompt
        balance_str = ""
        for network, assets in portfolio_balances.items():
            balance_str += f"{network}: {assets}\n"

        result = await chain.ainvoke(
            {
                "market_snapshot": market_snapshot.model_dump_json(),
                "portfolio_balances": balance_str,
            }
        )

        if isinstance(result, TradePlan):
            return result

        return cast(TradePlan, result)
