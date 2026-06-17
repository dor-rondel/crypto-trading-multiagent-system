"""
Tool for fetching on-chain whale movement data.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class WhaleProvider:
    """
    Provides on-chain data regarding large transactions and exchange flows.
    """

    async def get_whale_data(self, assets: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches recent large transactions.
        (Mock implementation for v2 demo).
        """
        flows = []
        for asset in assets:
            flows.append(
                {
                    "asset": asset,
                    "large_transfer_count_24h": 12 if asset == "BTC" else 5,
                    "net_exchange_flow_usd": -50000000 if asset == "ETH" else 2000000,
                    "sentiment": "accumulation" if asset == "ETH" else "neutral",
                }
            )
        return flows
