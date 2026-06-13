"""
LangGraph nodes for the trading workflow.
"""

import logging

from langgraph.graph import END

from src.agents.planner import PlannerAgent
from src.models.trading import TradePlan
from src.services.risk_validator import RiskValidator
from src.services.wallet_manager import WalletManager
from src.workflows.state import AgentState

logger = logging.getLogger(__name__)


async def planner_node(state: AgentState) -> AgentState:
    """
    Plan the next trading action based on market signals and portfolio state.
    """
    snapshot = state.get("market_snapshot")
    balances = state.get("portfolio_balances")

    if snapshot and balances:
        print(f"\n[PLANNER] Analyzing snapshot from {snapshot.source}...")
        agent = PlannerAgent()
        try:
            plan = await agent.plan(snapshot, balances)
            state["plan"] = plan
            print(f"[PLANNER] Rationale: {plan.rationale}")
            print(f"[PLANNER] Risk Level: {plan.risk_level}")
            for action in plan.actions:
                print(
                    f"  - {action.direction.upper()} {action.amount} "
                    f"{action.asset} on {action.chain}"
                )
        except Exception as e:
            logger.error("Error in PlannerAgent: %s", e)
            state["plan"] = TradePlan(
                rationale=f"Error generating plan: {e}", risk_level="high"
            )
    else:
        print("\n[PLANNER] Missing market data or balances.")

    state["next_step"] = "validator"
    return state


def validator_node(state: AgentState) -> AgentState:
    """
    Validate the proposed plan against deterministic constraints.
    """
    print("[VALIDATOR] Validating plan constraints...")
    plan = state.get("plan")
    balances = state.get("portfolio_balances")

    if not plan or not balances:
        print("[VALIDATOR] No plan or balances to validate.")
        state["approved_actions"] = []
        state["next_step"] = "executor"
        return state

    rv = RiskValidator()
    approved, status = rv.validate(plan, balances)

    state["approved_actions"] = approved
    print(f"[VALIDATOR] {status}")
    for action in approved:
        print(
            f"  - APPROVED: {action.direction.upper()} {action.amount} "
            f"{action.asset} on {action.chain}"
        )

    state["next_step"] = "executor"
    return state


async def executor_node(state: AgentState) -> AgentState:
    """
    Execute the validated plan using chain-specific adapters.
    """
    actions = state.get("approved_actions", [])
    if not actions:
        print("[EXECUTOR] No actions to execute.")
        state["next_step"] = END
        return state

    print(f"[EXECUTOR] Executing {len(actions)} actions...")

    # In a real LangGraph setup, we'd pass the WalletManager in config/state
    wm = WalletManager()
    await wm.initialize()

    for action in actions:
        try:
            print(f"[EXECUTOR] Dispatching {action.direction} on {action.chain}...")
            tx_hash = await wm.execute_swap(
                action.chain, action.direction, action.amount, action.asset
            )
            print(f"[EXECUTOR] Success! TX: {tx_hash}")
        except Exception as e:
            print(f"[EXECUTOR] Failed to execute {action.asset} on {action.chain}: {e}")

    state["next_step"] = END
    return state
