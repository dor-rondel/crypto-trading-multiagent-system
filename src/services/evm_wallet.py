"""
Service for managing EVM-specific wallet operations.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

from coinbase_agentkit import CdpEvmWalletProvider, CdpEvmWalletProviderConfig
from coinbase_agentkit.network import (
    CHAIN_ID_TO_NETWORK_ID,
    NETWORK_ID_TO_CHAIN,
)
from coinbase_agentkit.wallet_providers import (
    EthAccountWalletProvider,
    EthAccountWalletProviderConfig,
)
from eth_account import Account
from web3 import Web3

from src.constants.evm import (
    ERC20_ABI,
    NATIVE_WRAPPERS,
    ROUTER_ABI,
    ROUTER_ADDRESSES,
    USDC_CONTRACTS,
)
from src.services.base_wallet import BaseWallet
from src.utils.retry import retry_async

logger = logging.getLogger(__name__)


class EvmWallet(BaseWallet):
    """
    Handles EVM wallet operations using Coinbase CDP or local accounts.
    """

    def __init__(
        self,
        network_id: str,
        data_file: str,
        chain_id: Optional[str] = None,
        rpc_url: Optional[str] = None,
    ):
        self.network_id = network_id
        self.data_file = data_file
        self.chain_id = chain_id
        self.rpc_url = rpc_url
        self.provider: Any = None

    async def initialize(self) -> None:
        """
        Asynchronously initializes the EVM provider.
        """
        self.provider = await self._init_evm()

    async def _init_evm(self) -> Any:
        """
        Initializes an EVM wallet using Coinbase CDP or local key storage.
        """
        if self.chain_id and self.rpc_url:
            return self._init_custom_evm()
        return await self._init_cdp_evm()

    def _init_custom_evm(self) -> EthAccountWalletProvider:
        """
        Initializes a custom EVM wallet with local key storage.
        """
        str_chain_id = str(self.chain_id)
        CHAIN_ID_TO_NETWORK_ID[str_chain_id] = self.network_id

        if "ethereum-sepolia" in NETWORK_ID_TO_CHAIN:
            NETWORK_ID_TO_CHAIN[self.network_id] = NETWORK_ID_TO_CHAIN[
                "ethereum-sepolia"
            ]
        else:
            NETWORK_ID_TO_CHAIN[self.network_id] = next(
                iter(NETWORK_ID_TO_CHAIN.values())
            )

        local_private_key = None
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    local_private_key = data.get("private_key")
            except Exception as e:
                logger.warning(
                    "Failed to parse private key from %s: %s", self.data_file, e
                )

        if not local_private_key:
            # pylint: disable=no-value-for-parameter
            new_account = Account.create()
            local_private_key = new_account.key.hex()
            # pylint: enable=no-value-for-parameter
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({"private_key": local_private_key}, f)

        # pylint: disable=no-value-for-parameter
        account = Account.from_key(local_private_key)
        # pylint: enable=no-value-for-parameter
        config = EthAccountWalletProviderConfig(
            account=account, chain_id=str_chain_id, rpc_url=self.rpc_url
        )
        return EthAccountWalletProvider(config)

    async def _init_cdp_evm(self) -> CdpEvmWalletProvider:
        """
        Initializes an EVM wallet using Coinbase CDP.
        """
        key_file_path = os.getenv("CDP_API_KEY_FILE", "cdp_api_key.json")
        try:
            with open(key_file_path, "r", encoding="utf-8") as f:
                key_data = json.load(f)
                os.environ["CDP_API_KEY_ID"] = str(key_data.get("name", ""))
                os.environ["CDP_API_KEY_SECRET"] = str(
                    key_data.get("privateKey", "")
                ).replace("\\n", "\n")
        except FileNotFoundError:
            pass

        wallet_address = None
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    wallet_address = json.load(f).get("address")
            except Exception:
                pass

        config = CdpEvmWalletProviderConfig(network_id=self.network_id)
        if wallet_address:
            config.address = wallet_address
        else:
            config.idempotency_key = str(uuid.uuid4())

        loop = asyncio.get_running_loop()
        provider = await loop.run_in_executor(
            None, lambda: CdpEvmWalletProvider(config)
        )

        if wallet_address is None:
            wallet_address = provider.get_address()
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({"address": wallet_address}, f)

        return provider

    async def get_balances(self) -> Dict[str, float]:
        """
        Fetches native and USDC balances for the EVM wallet.
        """
        try:
            native_balance = await self._get_native_balance()
        except Exception:
            native_balance = 0.0

        try:
            usdc_balance = await self._get_usdc_balance()
        except Exception:
            usdc_balance = 0.0

        return {"native": native_balance, "usdc": usdc_balance}

    @retry_async(retries=3, delay=2.0)
    async def _get_native_balance(self) -> float:
        """Helper to fetch native balance with retry."""
        try:
            native_balance_raw = await asyncio.to_thread(self.provider.get_balance)
            return float(native_balance_raw or 0.0) / 10**18
        except Exception as e:
            logger.error(
                "Failed to fetch native balance for %s: %s", self.network_id, e
            )
            raise

    @retry_async(retries=3, delay=2.0)
    async def _get_usdc_balance(self) -> float:
        """Helper to fetch USDC balance with retry."""
        usdc_address = USDC_CONTRACTS.get(self.network_id)
        if not usdc_address:
            return 0.0

        try:
            balance_units = await asyncio.to_thread(
                self.provider.read_contract,
                contract_address=Web3.to_checksum_address(usdc_address),
                abi=ERC20_ABI,
                function_name="balanceOf",
                args=[Web3.to_checksum_address(self.get_address())],
            )
            return float(balance_units) / 10**6
        except Exception as e:
            logger.error("Failed to fetch USDC balance for %s: %s", self.network_id, e)
            raise

    async def swap_usdc_for_token(self, amount_usdc: float, token_symbol: str) -> str:
        """
        Executes a real swap: USDC -> Native (via Uniswap V3).
        """
        usdc_address = USDC_CONTRACTS.get(self.network_id)
        router_address = ROUTER_ADDRESSES.get(self.network_id)
        native_wrapper = NATIVE_WRAPPERS.get(self.network_id)

        if not usdc_address or not router_address or not native_wrapper:
            raise ValueError(f"Swap not supported on network: {self.network_id}")

        logger.info(
            "Executing swap: %.2f USDC for %s on %s",
            amount_usdc,
            token_symbol,
            self.network_id,
        )

        amount_in_units = int(amount_usdc * 10**6)

        # 1. Approve Router to spend USDC
        logger.info("Approving USDC spend...")
        try:
            # SDK send_transaction is known to conflict with main loop.
            # Using asyncio.to_thread to safely isolate its execution.
            await asyncio.to_thread(
                self.provider.send_transaction,
                {
                    "to": Web3.to_checksum_address(usdc_address),
                    "data": Web3()
                    .eth.contract(abi=ERC20_ABI)
                    .encode_abi(
                        "approve",
                        [Web3.to_checksum_address(router_address), amount_in_units],
                    ),
                },
            )
        except Exception as e:
            logger.error("Failed to approve USDC spend: %s", e)
            raise

        # 2. Execute Swap
        deadline = int(asyncio.get_event_loop().time() + 600)  # 10 minutes
        params = [
            Web3.to_checksum_address(usdc_address),
            Web3.to_checksum_address(native_wrapper),
            3000,  # 0.3% fee tier
            Web3.to_checksum_address(self.get_address()),
            deadline,
            amount_in_units,
            0,  # No slippage protection for testnet simulation
            0,
        ]

        try:
            tx_hash = await asyncio.to_thread(
                self.provider.send_transaction,
                {
                    "to": Web3.to_checksum_address(router_address),
                    "data": Web3()
                    .eth.contract(abi=ROUTER_ABI)
                    .encode_abi("exactInputSingle", [params]),
                },
            )
            return f"evm-{self.network_id}-tx-{tx_hash}"
        except Exception as e:
            logger.error("Failed to execute USDC -> Token swap: %s", e)
            raise

    async def swap_token_for_usdc(self, amount_token: float, token_symbol: str) -> str:
        """
        Executes a real swap: Native -> USDC (via Uniswap V3).
        """
        usdc_address = USDC_CONTRACTS.get(self.network_id)
        router_address = ROUTER_ADDRESSES.get(self.network_id)
        native_wrapper = NATIVE_WRAPPERS.get(self.network_id)

        if not usdc_address or not router_address or not native_wrapper:
            raise ValueError(f"Swap not supported on network: {self.network_id}")

        logger.info(
            "Executing swap: %.4f %s for USDC on %s",
            amount_token,
            token_symbol,
            self.network_id,
        )

        amount_in_units = int(amount_token * 10**18)

        deadline = int(asyncio.get_event_loop().time() + 600)
        params = [
            Web3.to_checksum_address(native_wrapper),
            Web3.to_checksum_address(usdc_address),
            3000,
            Web3.to_checksum_address(self.get_address()),
            deadline,
            amount_in_units,
            0,
            0,
        ]

        try:
            tx_hash = await asyncio.to_thread(
                self.provider.send_transaction,
                {
                    "to": Web3.to_checksum_address(router_address),
                    "value": amount_in_units,
                    "data": Web3()
                    .eth.contract(abi=ROUTER_ABI)
                    .encode_abi("exactInputSingle", [params]),
                },
            )
            return f"evm-{self.network_id}-tx-{tx_hash}"
        except Exception as e:
            logger.error("Failed to execute Token -> USDC swap: %s", e)
            raise

    @retry_async(retries=3, delay=1.0)
    async def get_transaction_status(self, tx_hash: str) -> Optional[str]:
        """
        Checks the status of an EVM transaction.
        """
        # Format is evm-{network_id}-tx-{hash}
        parts = tx_hash.split("-tx-")
        clean_hash = parts[-1]

        # Basic validation to avoid unnecessary retries on junk data
        if not clean_hash.startswith("0x") or len(clean_hash) < 64:
            logger.error("Fundamentally invalid EVM transaction hash: %s", clean_hash)
            return "FAILED"

        try:
            # receipt lookup can also cause loop issues or block.
            receipt = await asyncio.to_thread(
                self.provider.get_transaction_receipt, clean_hash
            )
            if receipt:
                if receipt.get("status") == 1:
                    return "CONFIRMED"
                return "FAILED"
        except Exception as e:
            logger.debug("EVM receipt not found for %s: %s", clean_hash, e)
            raise  # Re-raise to trigger retry

        return None

    def get_address(self) -> str:
        """Returns the address of the EVM wallet."""
        return str(self.provider.get_address())
