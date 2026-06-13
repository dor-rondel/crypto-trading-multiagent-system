from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.wallet_manager import WalletManager


@pytest.mark.asyncio
async def test_wallet_manager_dispatch():
    # Setup
    with (
        patch("src.services.wallet_manager.SolanaWallet") as mock_sol,
        patch("src.services.wallet_manager.EvmWallet") as mock_evm,
        patch("src.services.wallet_manager.Config"),
    ):
        # Mock wallets
        mock_sol_inst = MagicMock()
        mock_sol_inst.swap_usdc_for_token = AsyncMock(return_value="sol-tx")
        mock_sol.return_value = mock_sol_inst

        mock_evm_inst = MagicMock()
        mock_evm_inst.swap_usdc_for_token = AsyncMock(return_value="evm-tx")
        mock_evm_inst.initialize = AsyncMock()  # Add this
        mock_evm.return_value = mock_evm_inst

        # Initialize
        wm = WalletManager()
        # Mock _write_wallet_info_file to avoid file I/O
        with patch.object(wm, "_write_wallet_info_file"):
            await wm.initialize()

        # Test dispatch
        sol_tx = await wm.execute_swap("solana", "buy", 1.0, "SOL")
        evm_tx = await wm.execute_swap("sepolia", "buy", 1.0, "ETH")
        assert sol_tx == "sol-tx"
        assert evm_tx == "evm-tx"
        assert mock_sol_inst.swap_usdc_for_token.called
        assert mock_evm_inst.swap_usdc_for_token.called
