from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.aggregator import AggregatorAgent
from src.events.market_signal import AssetPrice, MarketSnapshot
from src.models.trading import TradeAction, TradeDirection, TradePlan


@pytest.mark.asyncio
async def test_planner_agent_plan():
    # Mock MarketSnapshot
    snapshot = MarketSnapshot(source="binance", assets={"SOL": AssetPrice(price=150.0)})
    balances = {"solana": {"usdc": 200.0, "native": 1.0}}

    # Mock AggregatorAgent to avoid needing a real GROQ_API_KEY
    with (
        patch("os.getenv", return_value="dummy_key"),
        patch("src.agents.aggregator.get_groq_llm"),
        patch("src.agents.aggregator.AGGREGATOR_PROMPT_TEMPLATE") as mock_prompt,
    ):
        mock_llm = MagicMock()
        with patch("src.agents.aggregator.get_groq_llm", return_value=mock_llm):
            mock_chain = MagicMock()
            mock_prompt.__or__.return_value = mock_chain
            mock_chain.ainvoke = AsyncMock(
                return_value=TradePlan(
                    actions=[],
                    rationale="test",
                    risk_level="low",
                )
            )

            agent = AggregatorAgent(model_name="test-model")
            result = await agent.plan(
                market_snapshot=snapshot, portfolio_balances=balances
            )

            assert result.rationale == "test"
        # Configure the mock chain's ainvoke method to return the TradePlan
        mock_chain.ainvoke = AsyncMock(
            return_value=TradePlan(
                actions=[
                    TradeAction(
                        chain="solana",
                        direction=TradeDirection.BUY,
                        amount=10.0,
                        asset="SOL",
                    )
                ],
                rationale="test",
                risk_level="low",
            )
        )

        # Ensure the agent's internal attribute points to our mock chain
        agent.structured_llm = mock_chain

        plan = await agent.plan(snapshot, balances)

        assert len(plan.actions) == 1
        assert plan.actions[0].asset == "SOL"
        assert plan.rationale == "test"
