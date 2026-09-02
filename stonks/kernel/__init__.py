"""Risk kernel — deterministic gates, sizing, regime, exits, structuring.

No LLM judgment enters here. Every number is config-driven and testable.
"""
from stonks.kernel.regime import evaluate_regime
from stonks.kernel.gates import evaluate_gates, snapshot_config
from stonks.kernel.sizing import size_structure
from stonks.kernel.structuring import pick_structure
from stonks.kernel.exits import check_exits

__all__ = [
    "evaluate_regime",
    "evaluate_gates",
    "snapshot_config",
    "size_structure",
    "pick_structure",
    "check_exits",
]
