"""Technical Analysis Tools"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _safe_float(value: Any) -> Optional[float]:
    """Convert to a JSON-safe float, or None for NaN/Infinity/missing values."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f):
        return None
    return f


class TechnicalAnalyzer:
    """Technical analysis calculations"""

    @staticmethod
    def calculate_sma(data: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=window).mean()

    @staticmethod
    def calculate_ema(data: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=window, adjust=False).mean()

    @staticmethod
    def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        # A flat price series (gain == loss == 0) produces a 0/0 NaN; that's
        # genuinely "no momentum", which RSI=50 represents.
        return rsi.fillna(50)

    @staticmethod
    def calculate_macd(
        data: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }

    @staticmethod
    def calculate_bollinger_bands(
        data: pd.Series,
        window: int = 20,
        num_std: float = 2
    ) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()

        upper = sma + (std * num_std)
        lower = sma - (std * num_std)

        return {
            "upper": upper,
            "middle": sma,
            "lower": lower,
        }

    @staticmethod
    def calculate_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 14
    ) -> pd.Series:
        """Average True Range"""
        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()

        return atr

    @staticmethod
    def calculate_volume_indicators(data: pd.DataFrame) -> Dict[str, Any]:
        """Volume-based indicators"""
        if 'Volume' not in data.columns:
            return {}

        volume = data['Volume']
        avg_20 = volume.rolling(window=20).mean().iloc[-1] if len(volume) >= 20 else None

        return {
            "avg_volume_20": _safe_float(avg_20),
            "avg_volume_50": _safe_float(volume.rolling(window=50).mean().iloc[-1]) if len(volume) >= 50 else None,
            "volume_ratio": _safe_float(volume.iloc[-1] / avg_20) if avg_20 else None,
        }

    @classmethod
    def analyze_all(cls, data: pd.DataFrame) -> Dict[str, Any]:
        """Run all technical analyses and return a compact, JSON-safe summary
        (latest values only - use `chart_series` for full historical series)."""
        if data.empty or len(data) < 20:
            return {"error": "Insufficient data for technical analysis"}

        close = data['Close']
        high = data['High']
        low = data['Low']

        macd = cls.calculate_macd(close, 12, 26, 9)
        bbands = cls.calculate_bollinger_bands(close, 20, 2)

        result = {
            "latest_price": _safe_float(close.iloc[-1]),
            "sma_20": _safe_float(cls.calculate_sma(close, 20).iloc[-1]) if len(close) >= 20 else None,
            "sma_50": _safe_float(cls.calculate_sma(close, 50).iloc[-1]) if len(close) >= 50 else None,
            "sma_200": _safe_float(cls.calculate_sma(close, 200).iloc[-1]) if len(close) >= 200 else None,
            "rsi": _safe_float(cls.calculate_rsi(close, 14).iloc[-1]) if len(close) >= 14 else None,
            "macd": {
                "macd": _safe_float(macd["macd"].iloc[-1]),
                "signal": _safe_float(macd["signal"].iloc[-1]),
                "histogram": _safe_float(macd["histogram"].iloc[-1]),
            },
            "bollinger_bands": {
                "upper": _safe_float(bbands["upper"].iloc[-1]),
                "middle": _safe_float(bbands["middle"].iloc[-1]),
                "lower": _safe_float(bbands["lower"].iloc[-1]),
            },
            "atr": _safe_float(cls.calculate_atr(high, low, close, 14).iloc[-1]) if len(close) >= 14 else None,
            "volume_indicators": cls.calculate_volume_indicators(data),
        }

        # Add price change
        if len(close) >= 2:
            result["price_change"] = {
                "1d": _safe_float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100),
                "1w": _safe_float((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100) if len(close) >= 6 else None,
                "1m": _safe_float((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21] * 100) if len(close) >= 21 else None,
                "3m": _safe_float((close.iloc[-1] - close.iloc[-63]) / close.iloc[-63] * 100) if len(close) >= 63 else None,
                "1y": _safe_float((close.iloc[-1] - close.iloc[-252]) / close.iloc[-252] * 100) if len(close) >= 252 else None,
            }

        # Add high/low
        result["high_low"] = {
            "52w_high": _safe_float(close.max()),
            "52w_low": _safe_float(close.min()),
            "current_vs_52w_high": _safe_float((close.iloc[-1] - close.max()) / close.max() * 100) if close.max() > 0 else None,
            "current_vs_52w_low": _safe_float((close.iloc[-1] - close.min()) / close.min() * 100) if close.min() > 0 else None,
        }

        return result

    @classmethod
    def chart_series(cls, data: pd.DataFrame, max_points: int = 180) -> List[Dict[str, Any]]:
        """Return a compact, JSON-safe time series for frontend charting
        (date, close, sma20/50, rsi, macd histogram) - trimmed to the most recent points."""
        if data.empty:
            return []

        close = data["Close"]
        sma20 = cls.calculate_sma(close, 20)
        sma50 = cls.calculate_sma(close, 50)
        rsi = cls.calculate_rsi(close, 14)
        macd = cls.calculate_macd(close, 12, 26, 9)

        dates = data.index if "Date" not in data.columns else data["Date"]

        points = []
        for i in range(len(data)):
            date_value = dates.iloc[i] if hasattr(dates, "iloc") else dates[i]
            points.append({
                "date": str(date_value)[:10],
                "close": _safe_float(close.iloc[i]),
                "sma_20": _safe_float(sma20.iloc[i]),
                "sma_50": _safe_float(sma50.iloc[i]),
                "rsi": _safe_float(rsi.iloc[i]),
                "macd_histogram": _safe_float(macd["histogram"].iloc[i]),
            })

        return points[-max_points:]
