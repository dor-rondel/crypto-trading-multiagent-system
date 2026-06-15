"""
Background service for monitoring pending blockchain transactions.
"""

import asyncio
import logging
from typing import Optional

from src.persistence.trade_history import TradeHistory
from src.services.wallet_manager import WalletManager

logger = logging.getLogger(__name__)


class TransactionMonitor:
    """
    Polls the blockchain for status updates on pending transactions.
    """

    def __init__(self, wallet_manager: WalletManager, interval: int = 30):
        self.wm = wallet_manager
        self.interval = interval
        self._is_running = False

    async def start(self) -> None:
        """Starts the monitoring loop."""
        if self._is_running:
            return
        self._is_running = True
        logger.info("Starting TransactionMonitor with interval=%ds", self.interval)

        try:
            while self._is_running:
                await self.check_pending_trades()
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            logger.info("TransactionMonitor cancelled.")
        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stops the monitoring loop."""
        self._is_running = False

    async def check_pending_trades(self) -> None:
        """Checks status for all pending trades in the database."""
        pending = await TradeHistory.get_pending_trades()
        if not pending:
            return

        logger.info("Checking %d pending transactions...", len(pending))

        for trade in pending:
            tx_hash = trade["tx_hash"]
            chain = trade["chain"]

            try:
                status = await self._query_blockchain_status(chain, tx_hash)
                if status:
                    await TradeHistory.update_status(tx_hash, status)
            except Exception as e:
                logger.error(
                    "Error checking status for %s on %s: %s", tx_hash, chain, e
                )

    async def _query_blockchain_status(self, chain: str, tx_hash: str) -> Optional[str]:
        """
        Queries the actual blockchain status.
        """
        wallet = self.wm.wallets.get(chain)
        if not wallet:
            logger.error("No wallet found for chain: %s", chain)
            return None

        return await wallet.get_transaction_status(tx_hash)
