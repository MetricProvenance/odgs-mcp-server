"""
detect_conflicts — Find contradictions between governance rules.

Wraps OdgsLlmBridge.detect_conflicts() to cross-reference rules from
multiple regulatory sources and surface semantic conflicts.

Tier: Pro
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def detect_conflicts(
    rules: list[dict[str, Any]],
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Analyze rules for semantic conflicts and contradictions.

    Args:
        rules: List of ODGS rule objects to analyze.
        provider: Optional LLM provider override.

    Returns:
        Dict with:
        - conflicts (list[dict]): Detected conflicts with affected rules and severity.
        - rules_analyzed (int): Number of rules analyzed.
        - conflict_count (int): Number of conflicts found.
        - error (str | None): Error message if analysis failed.
    """
    try:
        from odgs_llm import OdgsLlmBridge
    except ImportError:
        return {
            "conflicts": [],
            "rules_analyzed": len(rules),
            "conflict_count": 0,
            "error": "The `odgs-llm-bridge` package is not installed. Install: pip install odgs-mcp-server[llm]",
        }

    try:
        bridge = OdgsLlmBridge(provider=provider)
        conflicts = bridge.detect_conflicts(rules)

        return {
            "conflicts": conflicts,
            "rules_analyzed": len(rules),
            "conflict_count": len(conflicts),
            "error": None,
        }

    except Exception as e:
        logger.error("Conflict detection failed: %s", e)
        return {
            "conflicts": [],
            "rules_analyzed": len(rules),
            "conflict_count": 0,
            "error": f"Conflict detection failed: {type(e).__name__}: {e}",
        }
