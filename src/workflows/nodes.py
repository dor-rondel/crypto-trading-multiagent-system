"""
LangGraph nodes for the trading workflow.
"""

import logging

from langgraph.graph import END

from src.agents.planner import PlannerAgent
from src.models.trading import TradePlan
from src.persistence.trade_history import TradeHistory
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
        logger.info("Analyzing snapshot from %s...", snapshot.source)
        agent = PlannerAgent()
        try:
            plan = await agent.plan(snapshot, balances)
            state["plan"] = plan
            logger.info("Plan rationale: %s", plan.rationale)
            logger.info("Plan risk level: %s", plan.risk_level)
            for action in plan.actions:
                logger.info(
                    "Action proposed: %s %s %s on %s",
                    action.direction.upper(),
                    action.amount,
                    action.asset,
                    action.chain,
                )
        except Exception as e:
            logger.error("Error in PlannerAgent: %s", e)
            state["plan"] = TradePlan(
                rationale=f"Error generating plan: {e}", risk_level="high"
            )
    else:
        logger.warning("Missing market data or balances for planning.")

    state["next_step"] = "validator"
    return state


def validator_node(state: AgentState) -> AgentState:
    """
    Validate the proposed plan against deterministic constraints.
    """
    logger.info("Validating plan constraints...")
    plan = state.get("plan")
    balances = state.get("portfolio_balances")

    if not plan or not balances:
        logger.warning("No plan or balances to validate.")
        state["approved_actions"] = []
        state["next_step"] = "executor"
        return state

    rv = RiskValidator()
    approved, status = rv.validate(plan, balances)

    state["approved_actions"] = approved
    logger.info("Validation result: %s", status)
    for action in approved:
        logger.info(
            "Action APPROVED: %s %s %s on %s",
            action.direction.upper(),
            action.amount,
            action.asset,
            action.chain,
        )

    state["next_step"] = "executor"
    return state


async def executor_node(state: AgentState) -> AgentState:
    """
    Execute the validated plan using chain-specific adapters.
    """
    actions = state.get("approved_actions", [])
    plan = state.get("plan")
    if not actions:
        logger.info("No approved actions to execute.")
        state["next_step"] = END
        return state

    logger.info("Executing %d approved actions...", len(actions))

    # Access Singleton WalletManager
    wm = WalletManager()
    await wm.initialize()

    for action in actions:
        try:
            logger.info("Dispatching %s on %s...", action.direction, action.chain)
            tx_hash = await wm.execute_swap(
                action.chain, action.direction, action.amount, action.asset
            )
            logger.info("Execution successful. TX: %s", tx_hash)

            # Persist the trade as PENDING
            await TradeHistory.add_trade(
                tx_hash=tx_hash,
                chain=action.chain,
                asset=action.asset,
                direction=action.direction,
                amount=action.amount,
                status="PENDING",
                rationale=plan.rationale if plan else None,
            )

        except Exception as e:
            logger.error(
                "Failed to execute %s on %s: %s", action.asset, action.chain, e
            )

    state["next_step"] = END
    return state
