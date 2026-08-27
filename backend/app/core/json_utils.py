"""JSON-safety helpers.

Financial calculations routinely produce NaN/Infinity (e.g. 0/0 from a flat
return series, or a ratio with a zero denominator). Python's json module lets
those through by default, but Starlette's JSONResponse sets allow_nan=False
(correctly - NaN/Infinity aren't valid JSON), so any leaked into a response
body crashes the request with a 500. Rather than auditing every arithmetic
path for the last edge case, sanitize the response payload at the API
boundary.
"""
import math
from typing import Any


def sanitize_for_json(value: Any) -> Any:
    """Recursively replace non-finite floats (NaN/Infinity) with None."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_for_json(v) for v in value]
    return value
