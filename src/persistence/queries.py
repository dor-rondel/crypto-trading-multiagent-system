"""
Centralized SQL queries for the trading agent.
"""

# Table Initialization
# We include execution_price (price at time of trade)
# and cost_basis (total USDC value spent/received)
INIT_TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash TEXT UNIQUE,
    chain TEXT NOT NULL,
    asset TEXT NOT NULL,
    direction TEXT NOT NULL,
    amount float NOT NULL,
    execution_price float,
    cost_basis float,
    status TEXT NOT NULL,
    rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP
)
"""

# Trade Operations
INSERT_TRADE = """
INSERT INTO trades (
    tx_hash, chain, asset, direction, amount, 
    execution_price, cost_basis, status, rationale
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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

# PnL & Position Queries
# Returns sum of amount and weighted cost basis for confirmed trades
GET_POSITION_SUMMARY = """
SELECT 
    asset,
    SUM(CASE WHEN direction = 'buy' THEN amount ELSE -amount END) as net_amount,
    SUM(CASE WHEN direction = 'buy' THEN cost_basis ELSE -cost_basis END) as net_cost
FROM trades 
WHERE status = 'CONFIRMED'
GROUP BY asset
"""
