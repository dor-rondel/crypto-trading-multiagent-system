"""
Planner agent using Groq to generate structured trading plans.
"""

import os
from typing import Any, Dict, Optional, cast

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
        positions: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> TradePlan:
        """
        Generates a trading plan based on market data, current balances, and positions.
        """
        balance_str = self._format_balances(portfolio_balances)
        position_str = self._format_positions(market_snapshot, positions)

        chain = PLANNER_PROMPT_TEMPLATE | self.structured_llm
        result = await chain.ainvoke(
            {
                "market_snapshot": market_snapshot.model_dump_json(),
                "portfolio_balances": balance_str,
                "positions": position_str,
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

    def _format_positions(
        self, market_snapshot: MarketSnapshot, positions: Optional[Dict[str, Any]]
    ) -> str:
        """Formats positions and PnL for the prompt."""
        if not positions:
            return "None"

        lines = []
        for asset, data in positions.items():
            net_amount = data["net_amount"]
            net_cost = data["net_cost"]
            avg_price = net_cost / net_amount if net_amount > 0 else 0

            pnl_str = self._calculate_pnl_str(
                asset, market_snapshot, net_amount, avg_price
            )
            lines.append(
                f"{asset}: Amt={net_amount:.4f}, Avg=${avg_price:.2f}, PnL={pnl_str}"
            )

        return "\n".join(lines)

    def _calculate_pnl_str(
        self, asset: str, snapshot: MarketSnapshot, amount: float, avg_price: float
    ) -> str:
        """Calculates a string representation of PnL."""
        if asset not in snapshot.assets:
            return "Unknown"

        current_price = snapshot.assets[asset].price
        unrealized_pnl = (current_price - avg_price) * amount
        pnl_pct = (((current_price / avg_price) - 1) * 100) if avg_price > 0 else 0
        return f"${unrealized_pnl:.2f} ({pnl_pct:.2f}%)"
