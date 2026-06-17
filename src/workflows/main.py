"""
Main entry point for the crypto trading agent.
"""

import asyncio
import logging
from typing import Dict

from langchain_core.runnables import RunnableConfig

from src.config import Config
from src.events.market_signal import MarketSnapshot
from src.monitoring.logging_config import setup_logging
from src.persistence.db import init_db
from src.services.market_watcher import MarketWatcher
from src.services.transaction_monitor import TransactionMonitor
from src.services.wallet_manager import WalletManager
from src.workflows.graph import trading_app

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def wait_for_funding(wm: WalletManager) -> Dict[str, Dict[str, float]]:
    """
    Polls for balances until funds are detected.
    """
    logger.info("Checking for funds...")
    while True:
        current_balances = await wm.get_balances()
        has_funds = False

        logger.info("--- Current Portfolio Status ---")
        for network, assets in current_balances.items():
            logger.info(
                "[%s] Native: %.4f | USDC: %.2f",
                network.upper(),
                assets["native"],
                assets["usdc"],
            )
            if assets["native"] > 0 or assets["usdc"] > 0:
                has_funds = True

        if has_funds:
            logger.info("Funds detected! Proceeding to Stage 2 (Market Polling).")
            return current_balances

        logger.info("No funds detected. Retrying in 30 seconds...")
        await asyncio.sleep(30)


async def main() -> None:
    """
    Main entry point.
    """
    logger.info("🚀 Initializing Crypto Trading Agent...")
    Config.validate_config()

    # Initialize Database
    await init_db()

    # Initialize Wallet Manager
    wm_instance = WalletManager()
    await wm_instance.initialize()

    # Stage 1: Wait for funds
    await wait_for_funding(wm_instance)

    # Stage 2: Start Services

    # 1. Market Watcher
    watcher = MarketWatcher(assets=["ETH", "SOL", "AVAX"], interval=45)

    # 2. Transaction Monitor
    monitor = TransactionMonitor(wm_instance, interval=30)

    async def handle_snapshot(snapshot: MarketSnapshot) -> None:
        """
        Callback to trigger the workflow on new market snapshots.
        """
        logger.info("🔔 New Market Snapshot from %s", snapshot.source)

        # Checkpointer requires a thread_id in the config
        config: RunnableConfig = {"configurable": {"thread_id": "main_trading_loop"}}

        try:
            await trading_app.ainvoke(
                {
                    "messages": ["New market data received"],
                    "portfolio_balances": await wm_instance.get_balances(),
                    "market_snapshot": snapshot,
                    "next_step": "",
                    "plan": None,
                    "approved_actions": [],
                    "positions": None,
                    "gas_report": None,
                    "news_report": None,
                    "trend_report": None,
                    "performance_report": None,
                },
                config=config,
            )
        except Exception as e:
            logger.error("Error in trading workflow: %s", e)

    watcher.on_snapshot(handle_snapshot)

    # Run services in parallel
    logger.info("📈 Starting MarketWatcher and TransactionMonitor...")
    await asyncio.gather(watcher.start(), monitor.start())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Gracefully shutting down...")
