"""
LangGraph workflow definition for the multi-agent trading system.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.workflows.nodes import (
    aggregator_node,
    executor_node,
    gas_analyst_node,
    liquidity_analyst_node,
    news_analyst_node,
    performance_analyst_node,
    trend_analyst_node,
    validator_node,
)
from src.workflows.state import AgentState


def create_trading_graph() -> CompiledStateGraph:
    """
    Creates the LangGraph workflow for parallel multi-agent analysis and execution.
    """
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("gas_analyst", gas_analyst_node)
    workflow.add_node("news_analyst", news_analyst_node)
    workflow.add_node("trend_analyst", trend_analyst_node)
    workflow.add_node("performance_analyst", performance_analyst_node)
    workflow.add_node("liquidity_analyst", liquidity_analyst_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("executor", executor_node)

    # Research Spawner (Fan-out)
    workflow.add_node("research_spawner", lambda x: x)
    workflow.set_entry_point("research_spawner")

    # Fan-out
    workflow.add_edge("research_spawner", "gas_analyst")
    workflow.add_edge("research_spawner", "news_analyst")
    workflow.add_edge("research_spawner", "trend_analyst")
    workflow.add_edge("research_spawner", "performance_analyst")
    workflow.add_edge("research_spawner", "liquidity_analyst")

    # Fan-in (Aggregator waits for all analysts)
    workflow.add_edge("gas_analyst", "aggregator")
    workflow.add_edge("news_analyst", "aggregator")
    workflow.add_edge("trend_analyst", "aggregator")
    workflow.add_edge("performance_analyst", "aggregator")
    workflow.add_edge("liquidity_analyst", "aggregator")

    # Main chain
    workflow.add_edge("aggregator", "validator")
    workflow.add_edge("validator", "executor")
    workflow.add_edge("executor", END)

    # Setup Checkpointing (In-Memory for now to ensure compatibility)
    # Transition to persistent SqliteSaver once context management is refined.
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)


trading_app = create_trading_graph()
