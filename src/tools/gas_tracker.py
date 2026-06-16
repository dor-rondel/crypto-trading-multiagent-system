"""
Tool for fetching current gas prices across supported chains.
"""

import logging
from typing import Any, Dict

from solana.rpc.api import Client as SolanaClient
from web3 import Web3

from src.config import Config

logger = logging.getLogger(__name__)


class GasTracker:
    """
    Fetches gas prices and priority fees for multi-chain context.
    """

    def __init__(self) -> None:
        self.solana_client = SolanaClient(Config.SOLANA_RPC_URL)
        # Using RPCs from config
        self.eth_w3 = Web3(Web3.HTTPProvider(Config.SEPOLIA_RPC_URL))
        self.avax_w3 = Web3(
            Web3.HTTPProvider(
                Config.AVAX_FUJI_RPC_URL or "https://api.avax-test.network/ext/bc/C/rpc"
            )
        )

    async def get_all_gas_prices(self) -> Dict[str, Any]:
        """
        Fetches gas prices for all supported networks.
        """
        prices = {}

        # Ethereum Sepolia
        try:
            prices["sepolia"] = {
                "gas_price_gwei": Web3.from_wei(self.eth_w3.eth.gas_price, "gwei"),
                "unit": "Gwei",
            }
        except Exception as e:
            logger.error("Failed to fetch Sepolia gas: %s", e)
            prices["sepolia"] = {"error": str(e)}

        # Avalanche Fuji
        try:
            prices["avalanche-fuji"] = {
                "gas_price_gwei": Web3.from_wei(self.avax_w3.eth.gas_price, "gwei"),
                "unit": "Gwei",
            }
        except Exception as e:
            logger.error("Failed to fetch Fuji gas: %s", e)
            prices["avalanche-fuji"] = {"error": str(e)}

        # Solana Devnet - fallback to standard fee
        prices["solana"] = {
            "standard_fee_lamports": 5000,
            "unit": "lamports/signature",
        }

        return prices
