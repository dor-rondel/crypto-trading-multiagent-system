"""
Service for managing trade history records in SQLite.
"""

import logging
from datetime import datetime
from typing import List, Optional

import aiosqlite

from src.persistence.db import DB_PATH
from src.persistence.queries import (
    GET_PENDING_TRADES,
    INSERT_TRADE,
    UPDATE_TRADE_CONFIRMED,
    UPDATE_TRADE_STATUS,
)

logger = logging.getLogger(__name__)


class TradeHistory:
    """
    Handles CRUD operations for trades in the database.
    """

    @staticmethod
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    async def add_trade(
        tx_hash: str,
        chain: str,
        asset: str,
        direction: str,
        amount: float,
        status: str = "PENDING",
        rationale: Optional[str] = None,
    ) -> None:
        """Adds a new trade record."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                INSERT_TRADE,
                (tx_hash, chain, asset, direction, amount, status, rationale),
            )
            await db.commit()
            logger.info("Trade recorded: %s (%s)", tx_hash, status)

    @staticmethod
    async def update_status(tx_hash: str, status: str) -> None:
        """Updates the status of a trade and sets confirmed_at if appropriate."""
        async with aiosqlite.connect(DB_PATH) as db:
            if status in ["CONFIRMED", "FAILED"]:
                await db.execute(
                    UPDATE_TRADE_CONFIRMED,
                    (status, datetime.now().isoformat(), tx_hash),
                )
            else:
                await db.execute(UPDATE_TRADE_STATUS, (status, tx_hash))
            await db.commit()
            logger.info("Trade %s updated to %s", tx_hash, status)

    @staticmethod
    async def get_pending_trades() -> List[aiosqlite.Row]:
        """Returns a list of trades that are still PENDING."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_PENDING_TRADES) as cursor:
                rows = await cursor.fetchall()
                return list(rows)
