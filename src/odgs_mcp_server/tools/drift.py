"""
check_drift — Detect semantic drift in governance definitions.

Wraps OdgsLlmBridge.check_drift() to scan legislative definitions
for staleness, expired hashes, and outdated regulatory references.

Tier: Pro
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_drift(
    definitions_dir: str,
    threshold_days: int = 90,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Scan governance definitions for semantic drift.

    Args:
        definitions_dir: Path to the directory containing governance definitions.
        threshold_days: Number of days after which a definition is considered stale.
        provider: Optional LLM provider override.

    Returns:
        Dict with:
        - warnings (list[dict]): Drift warnings with severity and recommendations.
        - scanned_count (int): Number of definitions scanned.
        - stale_count (int): Number of stale definitions found.
        - error (str | None): Error message if scan failed.
    """
    try:
        from odgs_llm import OdgsLlmBridge
    except ImportError:
        return {
            "warnings": [],
            "scanned_count": 0,
            "stale_count": 0,
            "error": "The `odgs-llm-bridge` package is not installed. Install: pip install odgs-mcp-server[llm]",
        }

    try:
        bridge = OdgsLlmBridge(provider=provider)
        warnings = bridge.check_drift(definitions_dir, threshold_days=threshold_days)

        return {
            "warnings": warnings,
            "scanned_count": len(warnings),
            "stale_count": sum(1 for w in warnings if w.get("severity") in ("HIGH", "CRITICAL")),
            "threshold_days": threshold_days,
            "error": None,
        }

    except Exception as e:
        logger.error("Drift check failed: %s", e)
        return {
            "warnings": [],
            "scanned_count": 0,
            "stale_count": 0,
            "error": f"Drift check failed: {type(e).__name__}: {e}",
        }
