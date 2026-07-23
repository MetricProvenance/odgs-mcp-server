"""
flint — Integration with ODGS Commercial Flint Bridge.

Allows automated extraction of sovereign rules from raw regulation
text or repositories using the Flint Harvester capabilities.

Tier: Enterprise
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def harvest_sovereign_rules(
    source_text: str | None = None,
    source_url: str | None = None,
    harvester_type: str = "generic",
) -> dict[str, Any]:
    """
    Extract sovereign rules from regulation using the Flint Bridge.

    Args:
        source_text: Raw regulation text to harvest.
        source_url: URL to regulation source (alternative to text).
        harvester_type: Blueprint/harvester type (e.g., 'eu_ai_act', 'generic').

    Returns:
        Harvested ODGS rules and Sovereign Definition Pack metadata.
    """
    try:
        from odgs_commercial.harvester.factory import get_harvester
    except ImportError:
        return {
            "success": False,
            "error": "Flint Bridge requires the 'odgs-commercial' package. "
                     "Please contact sales@metricprovenance.com to acquire Enterprise access."
        }

    try:
        harvester = get_harvester(harvester_type)
        if not harvester:
            return {"success": False, "error": f"Harvester type '{harvester_type}' not found."}

        # PREVIEW / UNVERIFIED: odgs_commercial is a private package not available in
        # this (open-source) repo's test environment, so this call site can't be
        # exercised against the real harvester interface here. Treat this tool as
        # preview-quality until it's verified against an actual odgs_commercial build.
        result = harvester.harvest(text=source_text, url=source_url)
        return {
            "success": True,
            "harvester": harvester_type,
            "extracted_rules": result.get("rules", []),
            "metadata": result.get("metadata", {})
        }
    except Exception as e:
        logger.error("Flint harvesting failed: %s", e)
        return {"success": False, "error": str(e)}
