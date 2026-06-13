"""
Deterministic risk validation for trading plans.
"""

import logging
from typing import Dict, List, Tuple

from src.models.trading import TradeAction, TradeDirection, TradePlan

logger = logging.getLogger(__name__)


class RiskValidator:
    """
    Validates trade plans against portfolio constraints and risk rules.
    """

    def __init__(self, max_usdc_per_trade: float = 100.0):
        self.max_usdc_per_trade = max_usdc_per_trade

    def validate(
        self, plan: TradePlan, balances: Dict[str, Dict[str, float]]
    ) -> Tuple[List[TradeAction], str]:
        """
        Validates a trade plan. Returns a list of approved actions and a status message.
        """
        if not plan.actions:
            return [], "No actions to validate."

        approved_actions = []
        rejected_reasons = []

        for action in plan.actions:
            # 1. Check if chain exists in balances
            if action.chain not in balances:
                rejected_reasons.append(f"Unknown chain: {action.chain}")
                continue

            chain_balances = balances[action.chain]

            if action.direction == TradeDirection.BUY:
                # 2. Check USDC balance for BUY
                usdc_balance = chain_balances.get("usdc", 0.0)
                if action.amount > usdc_balance:
                    rejected_reasons.append(
                        f"Insufficient USDC on {action.chain}: "
                        f"{action.amount} > {usdc_balance}"
                    )
                    continue

                # 3. Check max trade limit
                if action.amount > self.max_usdc_per_trade:
                    rejected_reasons.append(
                        f"Trade amount {action.amount} exceeds limit "
                        f"{self.max_usdc_per_trade}"
                    )
                    continue

            elif action.direction == TradeDirection.SELL:
                # 4. Check asset balance for SELL
                # Note: 'native' is used as a proxy for the asset
                # In a real app, we'd check the specific token account balance.
                asset_balance = chain_balances.get("native", 0.0)
                if action.amount > asset_balance:
                    rejected_reasons.append(
                        f"Insufficient {action.asset} on {action.chain}: "
                        f"{action.amount} > {asset_balance}"
                    )
                    continue

            approved_actions.append(action)

        status = "All actions approved."
        if rejected_reasons:
            status = f"Some actions rejected: {'; '.join(rejected_reasons)}"
        elif not approved_actions:
            status = "All actions rejected."

        return approved_actions, status
