"""
Unit tests for TradeHistory persistence.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.persistence.trade_history import TradeHistory


@pytest.mark.asyncio
async def test_trade_history_add_trade():
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.__aenter__.return_value = mock_db
        mock_connect.return_value = mock_conn

        await TradeHistory.add_trade(
            tx_hash="0x1",
            chain="solana",
            asset="SOL",
            direction="BUY",
            amount=10.0,
            status="PENDING",
        )

        mock_db.execute.assert_awaited()
        mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_trade_history_update_status():
    with patch("aiosqlite.connect") as mock_connect:
        mock_db = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.__aenter__.return_value = mock_db
        mock_connect.return_value = mock_conn

        await TradeHistory.update_status("0x1", "CONFIRMED")

        mock_db.execute.assert_awaited()
        mock_db.commit.assert_awaited_once()
