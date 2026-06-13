"""
Main entry point for the crypto trading agent.
"""

import asyncio
import logging
from typing import Dict

from src.events.market_signal import MarketSnapshot
from src.monitoring.logging_config import setup_logging
from src.services.market_watcher import MarketWatcher
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

        print("\n--- Current Portfolio Status ---")
        for network, assets in current_balances.items():
            print(
                f"[{network.upper()}] Native: {assets['native']:.4f} | "
                f"USDC: {assets['usdc']:.2f}"
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
    print("🚀 Initializing Crypto Trading Agent...")

    # Initialize Wallet Manager
    wm_instance = WalletManager()
    await wm_instance.initialize()

    # Stage 1: Wait for funds
    await wait_for_funding(wm_instance)

    # Stage 2: Start Market Watcher
    watcher = MarketWatcher(assets=["ETH", "SOL", "AVAX"], interval=45)

    async def handle_snapshot(snapshot: MarketSnapshot) -> None:
        """
        Callback to trigger the workflow on new market snapshots.
        """
        print(f"\n🔔 New Market Snapshot from {snapshot.source}")
        await trading_app.ainvoke(
            {
                "messages": ["New market data received"],
                "portfolio_balances": await wm_instance.get_balances(),
                "market_snapshot": snapshot,
                "next_step": "",
                "plan": None,
                "approved_actions": [],
            }
        )

    watcher.on_snapshot(handle_snapshot)

    # Run the watcher loop
    await watcher.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Gracefully shutting down...")
