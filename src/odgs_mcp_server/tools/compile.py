"""
compile_regulation — Convert regulation text into ODGS rules.

Wraps OdgsLlmBridge.compile_regulation() to transform statute text,
SLA clauses, or regulatory articles into validated ODGS rule JSON.

Tier: Pro
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compile_regulation(
    regulation_text: str,
    regulation_name: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Convert regulation text into ODGS rule JSON objects.

    Args:
        regulation_text: The raw regulation text (statute, article, SLA clause).
        regulation_name: Optional name/identifier for the regulation.
        provider: Optional LLM provider override ("ollama", "google-genai", "openai-compat").

    Returns:
        Dict with:
        - rules (list[dict]): Generated ODGS rule objects.
        - regulation_name (str): Name of the regulation.
        - validation_status (str): Whether generated rules pass schema validation.
        - error (str | None): Error message if compilation failed.
    """
    try:
        from odgs_llm import OdgsLlmBridge
    except ImportError:
        return {
            "rules": [],
            "regulation_name": regulation_name,
            "validation_status": "ERROR",
            "error": (
                "The `odgs-llm-bridge` package is not installed. "
                "Install it with: pip install odgs-mcp-server[llm]"
            ),
        }

    try:
        bridge = OdgsLlmBridge(provider=provider)
        context = {"regulation_name": regulation_name} if regulation_name else None
        rules = bridge.compile_regulation(regulation_text, context=context)

        return {
            "rules": rules,
            "regulation_name": regulation_name or "unknown",
            "rule_count": len(rules),
            "validation_status": "VALID",
            "error": None,
        }

    except Exception as e:
        logger.error("Regulation compilation failed: %s", e)
        return {
            "rules": [],
            "regulation_name": regulation_name,
            "validation_status": "ERROR",
            "error": f"Compilation failed: {type(e).__name__}: {e}",
        }
