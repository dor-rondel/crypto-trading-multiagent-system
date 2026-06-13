"""
Definition of the agent state for LangGraph.
"""

from typing import Annotated, Dict, List, Optional, TypedDict

from src.events.market_signal import MarketSnapshot
from src.models.trading import TradeAction, TradePlan


class AgentState(TypedDict):
    """
    Represents the state of the agent workflow.
    """

    messages: Annotated[list[str], "The messages in the conversation"]
    portfolio_balances: Dict[str, Dict[str, float]]
    market_snapshot: Optional[MarketSnapshot]
    plan: Optional[TradePlan]
    approved_actions: List[TradeAction]
    next_step: str
