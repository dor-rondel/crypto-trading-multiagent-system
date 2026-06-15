"""
SQLite database setup and connection management for persistence.
"""

import logging
from pathlib import Path

import aiosqlite

from src.persistence.queries import INIT_TRADES_TABLE

logger = logging.getLogger(__name__)

DB_PATH = Path("trading_agent.db")


async def init_db() -> None:
    """
    Initializes the SQLite database and creates necessary tables.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        logger.info("Initializing database at %s", DB_PATH)
        await db.execute(INIT_TRADES_TABLE)
        await db.commit()


async def get_db_connection() -> aiosqlite.Connection:
    """
    Returns an async connection to the SQLite database.
    """
    return await aiosqlite.connect(DB_PATH)
