"""
Abstract base class for multi-chain wallets.
"""

from abc import ABC, abstractmethod
from typing import Dict


class BaseWallet(ABC):
    """
    Abstract base class defining the standard interface for all wallets.
    """

    @abstractmethod
    def get_address(self) -> str:
        """
        Returns the public address of the wallet.
        """

    @abstractmethod
    async def get_balances(self) -> Dict[str, float]:
        """
        Fetches the native and USDC balances for the wallet.
        """

    @abstractmethod
    async def swap_usdc_for_token(self, amount_usdc: float, token_symbol: str) -> str:
        """
        Swaps USDC for a target token. Returns transaction hash/id.
        """

    @abstractmethod
    async def swap_token_for_usdc(self, amount_token: float, token_symbol: str) -> str:
        """
        Swaps a token for USDC. Returns transaction hash/id.
        """
