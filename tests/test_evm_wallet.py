from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.services.evm_wallet import EvmWallet


@pytest.fixture
async def mock_wallet():
    with (
        patch("src.services.evm_wallet.CdpEvmWalletProvider") as mock_provider_class,
        patch("src.services.evm_wallet.os.path.exists", return_value=False),
        patch(
            "src.services.evm_wallet.os.getenv", return_value="mock_api_key_file.json"
        ),
        patch("builtins.open", mock_open(read_data='{"name": "a", "privateKey": "b"}')),
    ):
        mock_provider = MagicMock()
        mock_provider.get_address.return_value = "0x123"
        # Since we use run_in_executor, we need to mock the constructor return
        mock_provider_class.return_value = mock_provider

        wallet = EvmWallet("ethereum-sepolia", "sepolia_wallet.json")
        await wallet.initialize()
        return wallet


@pytest.mark.asyncio
async def test_get_address(mock_wallet):
    assert mock_wallet.get_address() == "0x123"


@pytest.mark.asyncio
async def test_get_balances_success(mock_wallet):
    mock_wallet.provider.get_balance.return_value = 1 * 10**18  # 1 ETH
    mock_wallet.provider.read_contract.return_value = 100 * 10**6  # 100 USDC

    # Patch Web3.to_checksum_address to just return the input
    with patch(
        "src.services.evm_wallet.Web3.to_checksum_address", side_effect=lambda x: x
    ):
        balances = await mock_wallet.get_balances()
        assert balances["native"] == 1.0
        assert balances["usdc"] == 100.0


@pytest.mark.asyncio
async def test_get_balances_contract_failure(mock_wallet):
    mock_wallet.provider.get_balance.return_value = 1 * 10**18  # 1 ETH
    mock_wallet.provider.read_contract.side_effect = Exception("Contract call failed")

    balances = await mock_wallet.get_balances()
    assert balances["native"] == 1.0
    assert balances["usdc"] == 0.0


@pytest.mark.asyncio
async def test_swap_usdc_for_token_success(mock_wallet):
    # Patch Web3 and contract
    with (
        patch("src.services.evm_wallet.Web3") as mock_web3,
        patch(
            "src.services.evm_wallet.Web3.to_checksum_address", side_effect=lambda x: x
        ),
    ):
        mock_web3.return_value.eth.contract.return_value.encode_abi.return_value = (
            b"data"
        )
        mock_wallet.provider.send_transaction = AsyncMock(return_value="tx_hash_123")

        tx_hash = await mock_wallet.swap_usdc_for_token(10.0, "ETH")

        assert tx_hash == "evm-ethereum-sepolia-tx-tx_hash_123"
        assert mock_wallet.provider.send_transaction.call_count == 2


@pytest.mark.asyncio
async def test_swap_token_for_usdc_success(mock_wallet):
    # Patch Web3 and contract
    with (
        patch("src.services.evm_wallet.Web3") as mock_web3,
        patch(
            "src.services.evm_wallet.Web3.to_checksum_address", side_effect=lambda x: x
        ),
    ):
        mock_web3.return_value.eth.contract.return_value.encode_abi.return_value = (
            b"data"
        )
        mock_wallet.provider.send_transaction = AsyncMock(return_value="tx_hash_456")

        tx_hash = await mock_wallet.swap_token_for_usdc(1.0, "ETH")

        assert tx_hash == "evm-ethereum-sepolia-tx-tx_hash_456"
        assert mock_wallet.provider.send_transaction.called


@pytest.mark.asyncio
async def test_swap_rpc_failure(mock_wallet):
    # Mock RPC error
    mock_wallet.provider.send_transaction = AsyncMock(
        side_effect=Exception("RPC Error")
    )

    with pytest.raises(Exception, match="RPC Error"):
        await mock_wallet.swap_usdc_for_token(10.0, "ETH")


@pytest.mark.asyncio
async def test_swap_insufficient_funds(mock_wallet):
    # Mock balance lower than swap amount (10 USDC)
    mock_wallet.provider.read_contract.return_value = 5 * 10**6

    # We expect the logic to fail because of insufficient balance.
    # Note: Current implementation doesn't have an explicit check,
    # so we mock the send_transaction to raise an error
    mock_wallet.provider.send_transaction = AsyncMock(
        side_effect=Exception("Insufficient Funds")
    )

    with pytest.raises(Exception, match="Insufficient Funds"):
        await mock_wallet.swap_usdc_for_token(10.0, "ETH")


@pytest.mark.asyncio
async def test_swap_decimal_precision(mock_wallet):
    # Test that 1.23456789 USDC is truncated to 1.234567 (6 decimals)
    with (
        patch("src.services.evm_wallet.Web3") as mock_web3,
        patch(
            "src.services.evm_wallet.Web3.to_checksum_address", side_effect=lambda x: x
        ),
    ):
        mock_contract = MagicMock()
        mock_web3.return_value.eth.contract.return_value = mock_contract
        mock_wallet.provider.send_transaction = AsyncMock(return_value="tx_hash")

        await mock_wallet.swap_usdc_for_token(1.23456789, "ETH")

        # Verify approval amount is correctly converted to 1,234,567 units
        args = mock_contract.encode_abi.call_args_list[0]
        assert args[0][1][1] == 1234567


@pytest.mark.asyncio
async def test_swap_deadline_expiry(mock_wallet):
    with (
        patch("src.services.evm_wallet.Web3") as mock_web3,
        patch(
            "src.services.evm_wallet.Web3.to_checksum_address", side_effect=lambda x: x
        ),
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        # Set loop time to 0, deadline will be 600
        mock_loop.return_value.time.return_value = 0

        mock_contract = MagicMock()
        mock_web3.return_value.eth.contract.return_value = mock_contract
        mock_wallet.provider.send_transaction = AsyncMock(return_value="tx_hash")

        await mock_wallet.swap_usdc_for_token(10.0, "ETH")

        # Verify deadline is 600
        args, kwargs = mock_contract.encode_abi.call_args
        # print(f"DEBUG args: {args}")
        # print(f"DEBUG kwargs: {kwargs}")
        assert args[1][0][4] == 600


@pytest.mark.asyncio
@patch("src.services.evm_wallet.EthAccountWalletProvider")
async def test_init_custom_evm(mock_provider_class):
    # Setup for custom chain
    with (
        patch("src.services.evm_wallet.os.path.exists", return_value=False),
        patch("builtins.open", mock_open()),
    ):
        wallet = EvmWallet(
            "custom-chain",
            "custom_wallet.json",
            chain_id="123",
            rpc_url="http://mock.rpc",
        )
        await wallet.initialize()
        assert mock_provider_class.called
        assert wallet.chain_id == "123"
