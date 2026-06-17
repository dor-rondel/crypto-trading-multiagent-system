"""
LangGraph nodes for the multi-agent trading workflow.
"""

import logging
from typing import Any, Dict

from langgraph.graph import END

from src.agents.aggregator import AggregatorAgent
from src.agents.subagents.gas_analyst import GasAnalyst
from src.agents.subagents.liquidity_analyst import LiquidityAnalyst
from src.agents.subagents.news_analyst import NewsAnalyst
from src.agents.subagents.performance_analyst import PerformanceAnalyst
from src.agents.subagents.trend_analyst import TrendAnalyst
from src.persistence.trade_history import TradeHistory
from src.services.risk_validator import RiskValidator
from src.services.wallet_manager import WalletManager
from src.tools.gas_tracker import GasTracker
from src.tools.liquidity_provider import LiquidityProvider
from src.tools.news_provider import NewsProvider
from src.workflows.state import AgentState

logger = logging.getLogger(__name__)


# --- Analyst Nodes ---


async def gas_analyst_node(state: AgentState) -> AgentState:
    """Evaluates network fees."""
    logger.info("Gas Analyst: Evaluating network fees...")
    tracker = GasTracker()
    try:
        gas_prices = await tracker.get_all_gas_prices()
        analyst = GasAnalyst()
        report = await analyst.analyze(gas_prices)
        state["gas_report"] = report
    except Exception as e:
        logger.error("Gas Analyst Error: %s", e)
    return state


async def news_analyst_node(state: AgentState) -> AgentState:
    """Evaluates macro sentiment."""
    logger.info("News Analyst: Evaluating market sentiment...")
    provider = NewsProvider()
    try:
        headlines = await provider.get_latest_headlines()
        analyst = NewsAnalyst()
        report = await analyst.analyze(headlines)
        state["news_report"] = report
    except Exception as e:
        logger.error("News Analyst Error: %s", e)
    return state


async def trend_analyst_node(state: AgentState) -> AgentState:
    """Evaluates technical trends."""
    logger.info("Trend Analyst: Evaluating market history...")
    snapshot = state.get("market_snapshot")
    if not snapshot:
        return state

    try:
        # Pass the snapshot containing history to the analyst
        history_str = snapshot.model_dump_json()
        analyst = TrendAnalyst()
        report = await analyst.analyze(history_str)
        state["trend_report"] = report
    except Exception as e:
        logger.error("Trend Analyst Error: %s", e)
    return state


async def performance_analyst_node(state: AgentState) -> AgentState:
    """Evaluates portfolio risk and PnL."""
    logger.info("Performance Analyst: Evaluating PnL risk...")
    positions = state.get("positions")
    snapshot = state.get("market_snapshot")
    if not positions or not snapshot:
        return state

    try:
        context_str = _format_pnl_context(positions, snapshot)
        analyst = PerformanceAnalyst()
        report = await analyst.analyze(context_str)
        state["performance_report"] = report
    except Exception as e:
        logger.error("Performance Analyst Error: %s", e)
    return state


async def liquidity_analyst_node(state: AgentState) -> AgentState:
    """Evaluates pool liquidity and slippage."""
    logger.info("Liquidity Analyst: Evaluating execution risk...")
    snapshot = state.get("market_snapshot")
    if not snapshot:
        return state

    provider = LiquidityProvider()
    try:
        metrics = await provider.get_liquidity_metrics(list(snapshot.assets.keys()))
        analyst = LiquidityAnalyst()
        report = await analyst.analyze(metrics)
        state["liquidity_report"] = report
    except Exception as e:
        logger.error("Liquidity Analyst Error: %s", e)
    return state


def _format_pnl_context(positions: Dict[str, Any], snapshot: Any) -> str:
    """Helper to format PnL context for the analyst."""
    lines = []
    for asset, data in positions.items():
        net_amount = data["net_amount"]
        net_cost = data["net_cost"]
        avg_price = net_cost / net_amount if net_amount > 0 else 0

        pnl_info = "Price Missing"
        if asset in snapshot.assets:
            cur_price = snapshot.assets[asset].price
            pnl = (cur_price - avg_price) * net_amount
            pnl_pct = ((cur_price / avg_price) - 1) * 100 if avg_price > 0 else 0
            pnl_info = f"${pnl:.2f} ({pnl_pct:.2f}%)"

        lines.append(
            f"{asset}: Amt={net_amount:.4f}, Avg=${avg_price:.2f}, PnL={pnl_info}"
        )
    return "\n".join(lines)


# --- Main Nodes ---


async def aggregator_node(state: AgentState) -> AgentState:
    """
    Plan the next trading action based on analyst reports.
    """
    snapshot = state.get("market_snapshot")
    balances = state.get("portfolio_balances")

    if snapshot and balances:
        try:
            state["positions"] = await TradeHistory.get_position_summaries()
        except Exception as e:
            logger.error("Failed to fetch position summaries: %s", e)

        agent = AggregatorAgent()
        try:
            state["plan"] = await agent.plan(
                market_snapshot=snapshot,
                portfolio_balances=balances,
                gas_report=state.get("gas_report"),
                news_report=state.get("news_report"),
                trend_report=state.get("trend_report"),
                performance_report=state.get("performance_report"),
                liquidity_report=state.get("liquidity_report"),
            )
            _log_proposed_actions(state["plan"])
        except Exception as e:
            logger.error("Error in AggregatorAgent: %s", e)

    state["next_step"] = "validator"
    return state


def _log_proposed_actions(plan: Any) -> None:
    """Helper to log proposed actions."""
    if not plan:
        return
    logger.info("Aggregator rationale: %s", plan.rationale)
    for action in plan.actions:
        logger.info(
            "Action proposed: %s %s %s on %s",
            action.direction.upper(),
            action.amount,
            action.asset,
            action.chain,
        )


def validator_node(state: AgentState) -> AgentState:
    """Validate the proposed plan."""
    plan = state.get("plan")
    balances = state.get("portfolio_balances")
    if not plan or not balances:
        state["approved_actions"] = []
        state["next_step"] = "executor"
        return state

    rv = RiskValidator()
    approved, status = rv.validate(plan, balances)
    state["approved_actions"] = approved
    logger.info("Validation result: %s", status)
    state["next_step"] = "executor"
    return state


async def executor_node(state: AgentState) -> AgentState:
    """Execute the validated plan."""
    actions = state.get("approved_actions", [])
    if not actions:
        state["next_step"] = END
        return state

    wm = WalletManager()
    await wm.initialize()

    for action in actions:
        await _execute_single_action(action, state)

    state["next_step"] = END
    return state


async def _execute_single_action(action: Any, state: AgentState) -> None:
    """Helper to execute and record a single action."""
    snapshot = state.get("market_snapshot")
    plan = state.get("plan")
    try:
        exec_price = (
            snapshot.assets[action.asset].price
            if snapshot and action.asset in snapshot.assets
            else 0.0
        )
        cost_basis = action.amount * exec_price

        wm = WalletManager()
        tx_hash = await wm.execute_swap(
            action.chain, action.direction, action.amount, action.asset
        )
        await TradeHistory.add_trade(
            tx_hash=tx_hash,
            chain=action.chain,
            asset=action.asset,
            direction=action.direction,
            amount=action.amount,
            execution_price=exec_price,
            cost_basis=cost_basis,
            status="PENDING",
            rationale=plan.rationale if plan else None,
        )
        logger.info("Executed %s on %s. TX: %s", action.asset, action.chain, tx_hash)
    except Exception as e:
        logger.error("Execution Failed: %s", e)
