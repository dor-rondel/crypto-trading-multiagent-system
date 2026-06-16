"""
Service for managing trade history records in SQLite.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import aiosqlite

from src.persistence.db import DB_PATH
from src.persistence.queries import (
    GET_PENDING_TRADES,
    GET_POSITION_SUMMARY,
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
        execution_price: Optional[float] = None,
        cost_basis: Optional[float] = None,
        status: str = "PENDING",
        rationale: Optional[str] = None,
    ) -> None:
        """Adds a new trade record with cost basis information."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                INSERT_TRADE,
                (
                    tx_hash,
                    chain,
                    asset,
                    direction,
                    amount,
                    execution_price,
                    cost_basis,
                    status,
                    rationale,
                ),
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

    @staticmethod
    async def get_position_summaries() -> Dict[str, Dict[str, float]]:
        """
        Calculates the current net amount and cost basis for all assets.
        Returns a dict mapping asset symbols to their summary.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_POSITION_SUMMARY) as cursor:
                rows = await cursor.fetchall()
                return {
                    row["asset"]: {
                        "net_amount": row["net_amount"],
                        "net_cost": row["net_cost"],
                    }
                    for row in rows
                }
