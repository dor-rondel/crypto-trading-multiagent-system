"""
Tool for calculating technical indicators using pandas-ta.
"""

import logging
from typing import Any, Dict, List

import pandas as pd

# pylint: disable=unused-import
import pandas_ta as ta  # noqa: F401

from src.events.market_signal import Candle

logger = logging.getLogger(__name__)


class TechnicalAnalysis:
    """
    Calculates technical indicators (RSI, MACD, EMAs) from OHLCV data.
    """

    def calculate_indicators(self, candles: List[Candle]) -> Dict[str, Any]:
        """
        Processes candles into technical indicators.
        """
        if not candles or len(candles) < 14:
            return {"error": "Insufficient data for technical analysis"}

        # Convert candles to DataFrame
        df = pd.DataFrame([c.model_dump() for c in candles])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        try:
            # 1. RSI (Relative Strength Index)
            df.ta.rsi(length=14, append=True)

            # 2. MACD (Moving Average Convergence Divergence)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)

            # 3. EMAs (Exponential Moving Averages)
            df.ta.ema(length=20, append=True)
            df.ta.ema(length=50, append=True)

            # Extract the last row of results
            last_row = df.iloc[-1]

            return {
                "rsi": round(float(last_row["RSI_14"]), 2)
                if "RSI_14" in last_row
                else None,
                "macd": {
                    "val": round(float(last_row["MACD_12_26_9"]), 4)
                    if "MACD_12_26_9" in last_row
                    else None,
                    "sig": round(float(last_row["MACDs_12_26_9"]), 4)
                    if "MACDs_12_26_9" in last_row
                    else None,
                    "hist": round(float(last_row["MACDh_12_26_9"]), 4)
                    if "MACDh_12_26_9" in last_row
                    else None,
                },
                "ema": {
                    "ema_20": round(float(last_row["EMA_20"]), 2)
                    if "EMA_20" in last_row
                    else None,
                    "ema_50": round(float(last_row["EMA_50"]), 2)
                    if "EMA_50" in last_row
                    else None,
                },
                "current_price": round(float(last_row["close"]), 2),
            }

        except Exception as e:
            logger.error("Error calculating technical indicators: %s", e)
            return {"error": str(e)}
