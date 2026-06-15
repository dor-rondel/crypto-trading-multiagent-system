import aiosqlite
import pytest

from src.persistence.db import DB_PATH, init_db
from src.persistence.trade_history import TradeHistory


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM trades")
        await db.commit()


@pytest.mark.asyncio
async def test_add_and_get_pending():
    await TradeHistory.add_trade("tx1", "solana", "SOL", "buy", 1.0)
    pending = await TradeHistory.get_pending_trades()
    assert len(pending) == 1
    assert pending[0]["tx_hash"] == "tx1"


@pytest.mark.asyncio
async def test_update_status_confirmed():
    await TradeHistory.add_trade("tx1", "solana", "SOL", "buy", 1.0)
    await TradeHistory.update_status("tx1", "CONFIRMED")
    pending = await TradeHistory.get_pending_trades()
    assert len(pending) == 0


@pytest.mark.asyncio
async def test_update_status_nonexistent():
    # Should not raise exception
    await TradeHistory.update_status("invalid_hash", "CONFIRMED")


@pytest.mark.asyncio
async def test_get_pending_empty():
    pending = await TradeHistory.get_pending_trades()
    assert len(pending) == 0
