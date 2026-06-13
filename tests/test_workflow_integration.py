from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langgraph.graph import END

from src.events.market_signal import AssetPrice, MarketSnapshot
from src.workflows.graph import create_trading_graph


@pytest.mark.asyncio
async def test_trading_workflow_integration():
    # Setup graph
    graph = create_trading_graph()

    # Define initial state
    initial_state = {
        "market_snapshot": MarketSnapshot(
            source="binance", assets={"SOL": AssetPrice(price=150.0)}
        ),
        "portfolio_balances": {"solana": {"usdc": 200.0, "native": 1.0}},
        "next_step": "planner",
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
            return_value=MagicMock(
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
        final_state = await graph.ainvoke(initial_state)

        # Assertions
        assert final_state["next_step"] == END
        assert mock_planner_instance.plan.called
        assert mock_validator_instance.validate.called
