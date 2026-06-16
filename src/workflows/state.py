"""
Definition of the agent state for LangGraph.
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph.message import add_messages

from src.events.market_signal import MarketSnapshot
from src.models.analysis import GasReport, NewsReport, PerformanceReport, TrendReport
from src.models.trading import TradeAction, TradePlan


class AgentState(TypedDict):
    """
    Represents the state of the agent workflow.
    """

    messages: Annotated[list[str], add_messages]
    portfolio_balances: Annotated[Dict[str, Dict[str, float]], lambda x, y: y]
    market_snapshot: Annotated[Optional[MarketSnapshot], lambda x, y: y]
    plan: Annotated[Optional[TradePlan], lambda x, y: y]
    approved_actions: Annotated[List[TradeAction], lambda x, y: y]
    next_step: Annotated[str, lambda x, y: y]
    positions: Annotated[Optional[Dict[str, Any]], lambda x, y: y]

    # Subagent Reports
    gas_report: Annotated[Optional[GasReport], lambda x, y: y]
    news_report: Annotated[Optional[NewsReport], lambda x, y: y]
    trend_report: Annotated[Optional[TrendReport], lambda x, y: y]
    performance_report: Annotated[Optional[PerformanceReport], lambda x, y: y]
