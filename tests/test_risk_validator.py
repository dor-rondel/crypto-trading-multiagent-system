from src.models.trading import TradeAction, TradeDirection, TradePlan
from src.services.risk_validator import RiskValidator


def test_risk_validator_approve_buy():
    validator = RiskValidator(max_usdc_per_trade=100.0)
    plan = TradePlan(
        actions=[
            TradeAction(
                chain="solana", direction=TradeDirection.BUY, amount=50.0, asset="SOL"
            )
        ],
        rationale="test",
        risk_level="low",
    )
    balances = {"solana": {"usdc": 100.0, "native": 1.0}}

    approved, status = validator.validate(plan, balances)
    assert len(approved) == 1
    assert status == "All actions approved."


def test_risk_validator_reject_insufficient_usdc():
    validator = RiskValidator(max_usdc_per_trade=100.0)
    plan = TradePlan(
        actions=[
            TradeAction(
                chain="solana", direction=TradeDirection.BUY, amount=150.0, asset="SOL"
            )
        ],
        rationale="test",
        risk_level="low",
    )
    balances = {"solana": {"usdc": 100.0, "native": 1.0}}

    approved, status = validator.validate(plan, balances)
    assert len(approved) == 0
    assert "Insufficient USDC" in status


def test_risk_validator_reject_max_limit():
    validator = RiskValidator(max_usdc_per_trade=100.0)
    plan = TradePlan(
        actions=[
            TradeAction(
                chain="solana", direction=TradeDirection.BUY, amount=110.0, asset="SOL"
            )
        ],
        rationale="test",
        risk_level="low",
    )
    balances = {"solana": {"usdc": 200.0, "native": 1.0}}

    approved, status = validator.validate(plan, balances)
    assert len(approved) == 0
    assert "exceeds limit" in status


def test_risk_validator_reject_unknown_chain():
    validator = RiskValidator(max_usdc_per_trade=100.0)
    plan = TradePlan(
        actions=[
            TradeAction(
                chain="unknown", direction=TradeDirection.BUY, amount=10.0, asset="SOL"
            )
        ],
        rationale="test",
        risk_level="low",
    )
    balances = {"solana": {"usdc": 200.0, "native": 1.0}}

    approved, status = validator.validate(plan, balances)
    assert len(approved) == 0
    assert "Unknown chain" in status
