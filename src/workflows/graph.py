"""
Definition of the LangGraph trading workflow.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.workflows.nodes import executor_node, planner_node, validator_node
from src.workflows.state import AgentState


def create_trading_graph() -> CompiledStateGraph:
    """
    Creates and compiles the trading workflow graph.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("executor", executor_node)

    workflow.set_entry_point("planner")

    workflow.add_edge("planner", "validator")
    workflow.add_edge("validator", "executor")
    workflow.add_edge("executor", END)

    return workflow.compile()


# Singleton instance
trading_app = create_trading_graph()
