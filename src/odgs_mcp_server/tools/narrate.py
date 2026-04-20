"""
narrate_audit — Convert S-Cert into human-readable narrative.

Wraps OdgsLlmBridge.narrate_audit() to transform cryptographic
audit certificates into plain-language narratives for different audiences.

Tier: Pro
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

VALID_AUDIENCES = ("executive", "legal", "technical", "auditor")


def narrate_audit(
    scert: dict[str, Any],
    audience: str = "executive",
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Convert an S-Cert into a human-readable narrative.

    Args:
        scert: The S-Cert JSON object (from a validation run).
        audience: Target audience — "executive", "legal", "technical", or "auditor".
        provider: Optional LLM provider override.

    Returns:
        Dict with:
        - narrative (str): The human-readable audit narrative.
        - audience (str): The target audience used.
        - error (str | None): Error message if narration failed.
    """
    if audience not in VALID_AUDIENCES:
        return {
            "narrative": "",
            "audience": audience,
            "error": f"Invalid audience '{audience}'. Must be one of: {', '.join(VALID_AUDIENCES)}",
        }

    try:
        from odgs_llm import OdgsLlmBridge
    except ImportError:
        return {
            "narrative": "",
            "audience": audience,
            "error": "The `odgs-llm-bridge` package is not installed. Install: pip install odgs-mcp-server[llm]",
        }

    try:
        bridge = OdgsLlmBridge(provider=provider)
        narrative = bridge.narrate_audit(scert, audience=audience)

        return {
            "narrative": narrative,
            "audience": audience,
            "verdict": scert.get("verdict", scert.get("execution_result", "UNKNOWN")),
            "error": None,
        }

    except Exception as e:
        logger.error("Audit narration failed: %s", e)
        return {
            "narrative": "",
            "audience": audience,
            "error": f"Narration failed: {type(e).__name__}: {e}",
        }
