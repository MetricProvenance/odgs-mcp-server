"""
validate_payload — Core ODGS validation tool.

Validates a data payload against governance rules using the OdgsInterceptor.
Returns pass/fail verdict with violations, warnings, and S-Cert audit data.

Tier: Community (free)
"""

from __future__ import annotations

import json
import logging
import traceback
from typing import Any

from odgs_mcp_server.tools._notice import certification_notice

logger = logging.getLogger(__name__)


def validate_payload(
    process_urn: str,
    data_context: dict[str, Any],
    project_root: str,
    required_integrity_hash: str | None = None,
    override_token: str | None = None,
) -> dict[str, Any]:
    """
    Validate a data payload against ODGS governance rules.

    Args:
        process_urn: The governance context URN (e.g., "urn:odgs:process:aml_check").
        data_context: The data payload to validate (key-value pairs).
        project_root: Path to the ODGS project root containing governance definitions.
        required_integrity_hash: Optional sovereign handshake hash for tamper detection.
        override_token: Optional token to override SOFT_STOP rules.

    Returns:
        A dict with:
        - valid (bool): Whether the payload passed all rules.
        - verdict (str): "APPROVED" or "BLOCKED".
        - violations (list[str]): List of rule violations.
        - warnings (list[str]): List of warnings (non-blocking).
        - s_cert (dict | None): The S-Cert audit trail if validation completed.
        - error (str | None): Error message if validation could not run.
    """
    try:
        from odgs import OdgsInterceptor, ProcessBlockedException
    except ImportError:
        return {
            "valid": False,
            "verdict": "ERROR",
            "violations": [],
            "warnings": [],
            "s_cert": None,
            "error": (
                "The `odgs` package is not installed. "
                "Install it with: pip install odgs>=6.0.0"
            ),
        }

    try:
        interceptor = OdgsInterceptor(project_root_path=project_root)

        # The interceptor returns True on success, raises on failure
        interceptor.intercept(
            process_urn=process_urn,
            data_context=data_context,
            required_integrity_hash=required_integrity_hash,
            override_token=override_token,
        )

        return {
            "valid": True,
            "verdict": "APPROVED",
            "violations": [],
            "warnings": [],
            "s_cert": {
                "status": "ISSUED",
                "process_urn": process_urn,
                "note": "Full S-Cert written to sovereign_audit.log",
            },
            "error": None,
            "_odgs_notice": certification_notice(),
        }

    except ProcessBlockedException as e:
        return {
            "valid": False,
            "verdict": "BLOCKED",
            "violations": [str(e)],
            "warnings": [],
            "s_cert": {
                "status": "ISSUED_WITH_VIOLATIONS",
                "process_urn": process_urn,
                "note": "Full S-Cert written to sovereign_audit.log",
            },
            "error": None,
            "_odgs_notice": certification_notice(),
        }

    except Exception as e:
        logger.error("Validation error: %s", traceback.format_exc())
        return {
            "valid": False,
            "verdict": "ERROR",
            "violations": [],
            "warnings": [],
            "s_cert": None,
            "error": f"Validation engine error: {type(e).__name__}: {e}",
        }


def validate_batch(
    items: list[dict[str, Any]],
    project_root: str,
    fail_fast: bool = False,
) -> dict[str, Any]:
    """
    Validate multiple payloads in a single call.

    Args:
        items: List of dicts, each with process_urn, data_context, and optional
               required_integrity_hash and override_token.
        project_root: Path to the ODGS project root.
        fail_fast: Stop on first failure.

    Returns:
        Summary with total/passed/failed counts and per-item results.
    """
    try:
        from odgs import OdgsInterceptor
    except ImportError:
        return {"error": "odgs package not installed", "total": len(items), "passed": 0, "failed": 0, "results": []}

    try:
        interceptor = OdgsInterceptor(project_root_path=project_root)
        result = interceptor.intercept_batch(items, fail_fast=fail_fast)
        return result
    except Exception as e:
        return {
            "error": f"Batch validation error: {e}",
            "total": len(items),
            "passed": 0,
            "failed": 0,
            "results": [],
        }
