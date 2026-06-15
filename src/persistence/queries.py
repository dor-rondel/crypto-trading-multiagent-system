"""
Centralized SQL queries for the trading agent.
"""

# Table Initialization
INIT_TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash TEXT UNIQUE,
    chain TEXT NOT NULL,
    asset TEXT NOT NULL,
    direction TEXT NOT NULL,
    amount float NOT NULL,
    status TEXT NOT NULL,
    rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP
)
"""

# Trade Operations
INSERT_TRADE = """
INSERT INTO trades (tx_hash, chain, asset, direction, amount, status, rationale)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_TRADE_STATUS = """
UPDATE trades SET status = ? WHERE tx_hash = ?
"""

UPDATE_TRADE_CONFIRMED = """
UPDATE trades SET status = ?, confirmed_at = ? WHERE tx_hash = ?
"""

GET_PENDING_TRADES = """
SELECT * FROM trades WHERE status = 'PENDING'
"""
