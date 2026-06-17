"""
Configuration management for the crypto-trading-agent.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Centralized configuration management using environment variables.
    """

    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    SEPOLIA_RPC_URL = os.getenv("ETH_SEPOLIA_RPC_URL", "https://rpc.sepolia.org")
    SEPOLIA_WALLET_DATA_FILE = os.getenv(
        "SEPOLIA_WALLET_DATA_FILE", "sepolia_wallet.json"
    )
    FUJI_WALLET_DATA_FILE = os.getenv("FUJI_WALLET_DATA_FILE", "fuji_wallet.json")
    AVAX_FUJI_RPC_URL = os.getenv("AVAX_FUJI_RPC_URL")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")

    # Enforce strict model configuration, skip if running tests
    GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
    if not GROQ_MODEL_NAME and not os.environ.get("PYTEST_CURRENT_TEST"):
        print(
            "ERROR: GROQ_MODEL_NAME environment variable is not set.", file=sys.stderr
        )
        sys.exit(1)
