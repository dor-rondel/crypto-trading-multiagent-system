from unittest.mock import AsyncMock, patch

import pytest
from langgraph.graph import END

from src.models.trading import TradeAction, TradeDirection
from src.workflows.nodes import executor_node


@pytest.mark.asyncio
async def test_executor_node_success():
    state = {
        "approved_actions": [
            TradeAction(
                chain="solana", direction=TradeDirection.BUY, amount=1.0, asset="SOL"
            )
        ]
    }

    # Mock WalletManager
    with patch("src.workflows.nodes.WalletManager") as mock_wm_class:
        mock_wm = mock_wm_class.return_value
        mock_wm.initialize = AsyncMock()
        mock_wm.execute_swap = AsyncMock(return_value="tx_hash_123")

        updated_state = await executor_node(state)

        assert updated_state["next_step"] == END
        assert mock_wm.execute_swap.called
        assert mock_wm.execute_swap.call_args[0] == ("solana", "buy", 1.0, "SOL")


@pytest.mark.asyncio
async def test_executor_node_no_actions():
    state = {"approved_actions": []}

    updated_state = await executor_node(state)

    assert updated_state["next_step"] == END
