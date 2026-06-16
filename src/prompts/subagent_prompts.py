"""
Prompts for specialized subagents.
"""

from langchain_core.prompts import ChatPromptTemplate

# Gas Analyst Prompts
GAS_SYSTEM_PROMPT = (
    "You are a Network Fee Analyst. "
    "Analyze current gas prices and priority fees across chains.\n"
    "Identify if network conditions are favorable for trading or if high fees "
    "could eat into profits. Provide a recommendation: PROCEED or WAIT."
)
GAS_HUMAN_PROMPT = "Current Network Fees: {gas_prices}"
GAS_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", GAS_SYSTEM_PROMPT),
        ("human", GAS_HUMAN_PROMPT),
    ]
)

# News Analyst Prompts
NEWS_SYSTEM_PROMPT = (
    "You are a Crypto Macro Analyst. "
    "Analyze recent news headlines and identify the prevailing market sentiment.\n"
    "Classify sentiment as BULLISH, BEARISH, or NEUTRAL and provide a brief summary."
)
NEWS_HUMAN_PROMPT = "Recent Headlines: {headlines}"
NEWS_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", NEWS_SYSTEM_PROMPT),
        ("human", NEWS_HUMAN_PROMPT),
    ]
)

# Trend Analyst Prompts
TREND_SYSTEM_PROMPT = (
    "You are a Technical Trend Analyst. "
    "Analyze historical OHLCV data (history) to identify short-term trends "
    "for each asset (e.g., UPTREND, DOWNTREND, BREAKOUT, SIDEWAYS)."
)
TREND_HUMAN_PROMPT = "Market History: {market_history}"
TREND_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", TREND_SYSTEM_PROMPT),
        ("human", TREND_HUMAN_PROMPT),
    ]
)

# Performance Analyst Prompts
PERFORMANCE_SYSTEM_PROMPT = (
    "You are a Portfolio Risk Analyst. "
    "Analyze current positions and unrealized PnL to evaluate risk.\n"
    "Identify if any stop-loss triggers are near or if profit-taking is warranted.\n"
    "Provide a status: HEALTHY, STOP_LOSS_WARNING, or TAKE_PROFIT_READY."
)
PERFORMANCE_HUMAN_PROMPT = "Current Positions & PnL: {positions}"
PERFORMANCE_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", PERFORMANCE_SYSTEM_PROMPT),
        ("human", PERFORMANCE_HUMAN_PROMPT),
    ]
)
