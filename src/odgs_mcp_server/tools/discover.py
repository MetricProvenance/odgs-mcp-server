"""
discover_bindings — Generate physical data mappings from catalog metadata.

Wraps OdgsLlmBridge.discover_bindings() to auto-generate
physical_data_map.json bindings from data catalog metadata.

Tier: Pro
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def discover_bindings(
    catalog_metadata: dict[str, Any],
    metrics: list[dict[str, Any]] | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Generate physical data mappings from catalog metadata.

    Given data catalog metadata (column names, types, descriptions),
    generates a physical_data_map.json binding to ODGS metrics.

    Args:
        catalog_metadata: Data catalog metadata (tables, columns, descriptions).
        metrics: Optional list of ODGS metric definitions to bind against.
        provider: Optional LLM provider override.

    Returns:
        Dict with:
        - bindings (dict): Generated physical_data_map.json content.
        - mapped_count (int): Number of mappings generated.
        - error (str | None): Error message if discovery failed.
    """
    try:
        from odgs_llm import OdgsLlmBridge
    except ImportError:
        return {
            "bindings": {},
            "mapped_count": 0,
            "error": "The `odgs-llm-bridge` package is not installed. Install: pip install odgs-mcp-server[llm]",
        }

    try:
        bridge = OdgsLlmBridge(provider=provider)
        bindings = bridge.discover_bindings(catalog_metadata, metrics=metrics)

        mapped_count = len(bindings.get("mappings", []))
        return {
            "bindings": bindings,
            "mapped_count": mapped_count,
            "error": None,
        }

    except Exception as e:
        logger.error("Binding discovery failed: %s", e)
        return {
            "bindings": {},
            "mapped_count": 0,
            "error": f"Binding discovery failed: {type(e).__name__}: {e}",
        }
