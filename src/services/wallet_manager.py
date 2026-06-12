"""
Orchestrator for managing multi-chain wallets.
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv
from solana.rpc.api import Client

from src.services.evm_wallet import EvmWallet
from src.services.solana_wallet import SolanaWallet

load_dotenv()


class WalletManager:
    """
    Orchestrates wallet lifecycle across supported chains.
    """

    def __init__(self) -> None:
        """
        Initialize the WalletManager and load/create wallets for all chains.
        """
        sol_client = Client(
            os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"), timeout=60
        )
        self.wallets: Dict[str, Any] = {
            "solana": SolanaWallet(sol_client),
            "sepolia": EvmWallet(
                "ethereum-sepolia",
                os.getenv("SEPOLIA_WALLET_DATA_FILE", "sepolia_wallet.json"),
            ),
            "avalanche-fuji": EvmWallet(
                "avalanche-fuji",
                os.getenv("FUJI_WALLET_DATA_FILE", "fuji_wallet.json"),
                chain_id="43113",
                rpc_url="https://avalanche-fuji.infura.io/v3/bec088a5e4bc4c459a346f52f3492252",
            ),
        }
        self._write_wallet_info_file()

    def get_address(self, network_id: str) -> str:
        """
        Returns the address of a wallet for a given network.
        """
        wallet = self.wallets.get(network_id)
        return wallet.get_address() if wallet else "ERROR"

    def _write_wallet_info_file(self) -> None:
        """
        Writes public wallet information and funding instructions to WALLETS.md.
        """
        info = "# Wallet Information & Funding Instructions\n\n"
        info += "Use the following to fund wallets\n"
        info += "with testnet Native tokens and USDC.\n\n"

        # Solana
        sol = self.wallets.get("solana")
        info += "### Solana Devnet\n"
        if isinstance(sol, SolanaWallet):
            info += f"- **Address:** `{sol.get_address()}`\n"
            info += f"- **Private Key:** `{sol.get_private_key_b58()}`\n"
        else:
            info += "- **Address:** `ERROR`\n"
            info += "- **Private Key:** `ERROR`\n"
        info += "- **Faucet:** [Solana Faucet](https://faucet.solana.com/)\n\n"

        # EVM
        for network in ["sepolia", "avalanche-fuji"]:
            wallet = self.wallets.get(network)
            info += f"### {network.capitalize()}\n"
            addr = wallet.get_address() if isinstance(wallet, EvmWallet) else "ERROR"
            info += f"- **Address:** `{addr}`\n"
            info += "- **Faucet:** [Coinbase Faucet]"
            info += "(https://www.coinbase.com/faucets)\n\n"

        info += "---\n"
        info += "*Note: Private keys are included here for testnet convenience.*\n"

        with open("WALLETS.md", "w", encoding="utf-8") as f:
            f.write(info)

    def get_balances(self) -> Dict[str, Dict[str, float]]:
        """
        Fetches balances for all wallets.
        """
        return {name: wallet.get_balances() for name, wallet in self.wallets.items()}
