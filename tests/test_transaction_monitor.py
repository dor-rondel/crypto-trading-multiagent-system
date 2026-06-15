from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.transaction_monitor import TransactionMonitor


@pytest.mark.asyncio
async def test_transaction_monitor_polling_no_pending():
    # Setup
    mock_wm = MagicMock()
    monitor = TransactionMonitor(mock_wm, interval=0.1)

    # Mock TradeHistory to return empty list
    with patch(
        "src.services.transaction_monitor.TradeHistory.get_pending_trades",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = []

        await monitor.check_pending_trades()
        mock_get.assert_awaited_once()


@pytest.mark.asyncio
async def test_transaction_monitor_status_failed():
    # Setup
    mock_wm = MagicMock()
    mock_wm.wallets = {}
    monitor = TransactionMonitor(mock_wm, interval=0.1)

    with patch(
        "src.services.transaction_monitor.TradeHistory.get_pending_trades",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = [{"tx_hash": "tx_fail", "chain": "solana"}]

        # Mock wallet and status check
        mock_wallet = AsyncMock()
        mock_wallet.get_transaction_status.return_value = "FAILED"
        mock_wm.wallets["solana"] = mock_wallet

        with patch(
            "src.services.transaction_monitor.TradeHistory.update_status",
            new_callable=AsyncMock,
        ) as mock_update:
            await monitor.check_pending_trades()

            mock_wallet.get_transaction_status.assert_awaited_once_with("tx_fail")
            mock_update.assert_awaited_once_with("tx_fail", "FAILED")


@pytest.mark.asyncio
async def test_transaction_monitor_wallet_missing():
    # Setup
    mock_wm = MagicMock()
    mock_wm.wallets = {}  # Empty wallet map
    monitor = TransactionMonitor(mock_wm, interval=0.1)

    with patch(
        "src.services.transaction_monitor.TradeHistory.get_pending_trades",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = [{"tx_hash": "tx1", "chain": "unknown_chain"}]

        # Should not raise exception
        await monitor.check_pending_trades()
        # Verify no status check called
        assert len(mock_wm.wallets) == 0
