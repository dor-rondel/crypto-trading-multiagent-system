from unittest.mock import AsyncMock, patch

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END

from src.events.market_signal import AssetPrice, MarketSnapshot
from src.models.trading import TradePlan
from src.workflows.graph import create_trading_graph


@pytest.mark.asyncio
async def test_workflow_persistence_and_resumption():
    # Setup graph with checkpointer
    checkpointer = MemorySaver()
    graph = create_trading_graph()
    compiled_graph = graph.builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "test_thread"}}

    # Define initial state
    initial_state = {
        "market_snapshot": MarketSnapshot(
            source="binance", assets={"SOL": AssetPrice(price=150.0)}
        ),
        "portfolio_balances": {"solana": {"usdc": 200.0, "native": 1.0}},
    }

    # Mock all external dependencies
    with (
        patch("src.workflows.nodes.PlannerAgent") as mock_planner,
        patch("src.workflows.nodes.RiskValidator") as mock_validator,
        patch("src.workflows.nodes.WalletManager") as mock_wm,
    ):
        # Planner mock
        mock_planner_instance = mock_planner.return_value
        mock_planner_instance.plan = AsyncMock(
            return_value=TradePlan(
                actions=[],  # Empty actions to test flow
                rationale="test",
                risk_level="low",
            )
        )

        # Validator mock
        mock_validator_instance = mock_validator.return_value
        mock_validator_instance.validate.return_value = ([], "All approved")

        # Executor mock
        mock_wm_instance = mock_wm.return_value
        mock_wm_instance.initialize = AsyncMock()

        # Run graph
        await compiled_graph.ainvoke(initial_state, config=config)

    # Verify checkpoint exists
    checkpoint = await checkpointer.aget(config)
    assert checkpoint is not None

    # Verify we can load state from checkpoint
    snapshot = await compiled_graph.aget_state(config)
    assert snapshot.values["next_step"] == END  # After planner/validator/executor
