"""
ODGS MCP Server — main entry point.

Registers all tools with FastMCP and starts the server.
Run via: odgs-mcp-server --transport stdio
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from odgs_mcp_server import __version__
from odgs_mcp_server.config import ServerConfig
from odgs_mcp_server.auth import AuthGate

# ── Server Setup ──────────────────────────────────────────────────

logger = logging.getLogger("odgs_mcp_server")

mcp = FastMCP(
    "ODGS Governance Server",
    instructions=(
        "Open Data Governance Standard — runtime governance enforcement for AI agents. "
        "Validate data payloads, compile regulations into rules, detect semantic drift, "
        "and generate cryptographic audit trails (S-Certs). "
        f"Version: {__version__}"
    ),
)

# Global state — initialized in main()
_config: ServerConfig | None = None
_auth: AuthGate | None = None


def _get_config() -> ServerConfig:
    global _config
    if _config is None:
        _config = ServerConfig.from_env()
    return _config


def _get_auth() -> AuthGate:
    global _auth
    if _auth is None:
        cfg = _get_config()
        _auth = AuthGate(
            api_key=cfg.api_key,
            registry_url=cfg.registry_url,
            cache_dir=cfg.cache_dir,
        )
    return _auth


def _check_tier(tool_name: str) -> str | None:
    """Check if current tier can access tool. Returns error message or None."""
    auth = _get_auth()
    if not auth.check_access(tool_name):
        return auth.upgrade_message(tool_name)
    return None


# ── Community Tools ───────────────────────────────────────────────


@mcp.tool()
def validate_payload(
    process_urn: str,
    data_context: dict[str, Any],
    project_root: str | None = None,
    required_integrity_hash: str | None = None,
    override_token: str | None = None,
) -> str:
    """Validate a data payload against ODGS governance rules.

    Runs the payload through the Sovereign Validation Engine and returns
    a pass/fail verdict with violations, warnings, and S-Cert audit data.

    Args:
        process_urn: Governance context URN (e.g., "urn:odgs:process:aml_check").
        data_context: The data payload to validate (key-value pairs).
        project_root: Path to ODGS project root. Defaults to $ODGS_PROJECT_ROOT or cwd.
        required_integrity_hash: Optional sovereign handshake hash for tamper detection.
        override_token: Optional token to override SOFT_STOP rules.
    """
    gate_error = _check_tier("validate_payload")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.validate import validate_payload as _validate

    root = project_root or _get_config().project_root
    result = _validate(
        process_urn=process_urn,
        data_context=data_context,
        project_root=root,
        required_integrity_hash=required_integrity_hash,
        override_token=override_token,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def validate_batch(
    items: list[dict[str, Any]],
    project_root: str | None = None,
    fail_fast: bool = False,
) -> str:
    """Validate multiple data payloads in a single call.

    Each item should have: process_urn (str), data_context (dict),
    and optionally required_integrity_hash and override_token.

    Args:
        items: List of payloads to validate.
        project_root: Path to ODGS project root. Defaults to $ODGS_PROJECT_ROOT or cwd.
        fail_fast: Stop on first failure if True.
    """
    gate_error = _check_tier("validate_payload")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.validate import validate_batch as _batch

    root = project_root or _get_config().project_root
    result = _batch(items=items, project_root=root, fail_fast=fail_fast)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def list_packs(
    project_root: str | None = None,
) -> str:
    """List all available ODGS Certified Packs.

    Shows which regulation-specific rule bundles are available and
    which are installed locally. Certified Packs include EU AI Act,
    DORA, CSRD, GDPR, NIS2, Basel III, and more.

    Args:
        project_root: Path to ODGS project root. Defaults to $ODGS_PROJECT_ROOT or cwd.
    """
    gate_error = _check_tier("list_packs")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.packs import list_packs as _list

    cfg = _get_config()
    root = project_root or cfg.project_root
    result = _list(project_root=root, cache_dir=cfg.cache_dir)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def download_pack(
    pack_id: str,
) -> str:
    """Download a Certified Regulation Pack to the local cache.

    Requires Pro tier or higher. Fetches the pack JSON from the registry
    and stores it in the local cache directory for fast local validations.

    Args:
        pack_id: The ID of the pack to download (e.g., "eu-ai-act", "sample-pack").
    """
    gate_error = _check_tier("compile_regulation") # Requires Pro tier
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.packs import download_pack as _download

    cfg = _get_config()
    auth = _get_auth()
    
    result = _download(
        pack_id=pack_id,
        registry_url=cfg.registry_url,
        cache_dir=cfg.cache_dir,
        api_key=auth.api_key,
    )
    return json.dumps(result, indent=2, default=str)



@mcp.tool()
def governance_score(
    project_root: str | None = None,
) -> str:
    """Score a project's governance maturity (0-100).

    Analyzes the ODGS project configuration across four categories:
    Legislative (ontology, metrics), Judiciary (rules, signing),
    Executive (bindings, physical maps), and Infrastructure (crypto, schemas).

    Returns a letter grade (A-F) with specific findings and recommendations.

    Args:
        project_root: Path to ODGS project root. Defaults to $ODGS_PROJECT_ROOT or cwd.
    """
    gate_error = _check_tier("governance_score")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.score import governance_score as _score

    root = project_root or _get_config().project_root
    result = _score(project_root=root)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def conformance_check(
    level: str = "L1",
    project_root: str | None = None,
) -> str:
    """Run an ODGS conformance self-check.

    Verifies that the governance project meets ODGS conformance requirements.
    L1 checks file existence; L2 adds cross-referencing and sovereign hash validation.

    Args:
        level: Conformance level — "L1" (basic) or "L2" (full).
        project_root: Path to ODGS project root. Defaults to $ODGS_PROJECT_ROOT or cwd.
    """
    gate_error = _check_tier("conformance_check")
    if gate_error:
        return gate_error

    try:
        from odgs import OdgsInterceptor, ConformanceException
    except ImportError:
        return json.dumps({"error": "odgs package not installed"})

    root = project_root or _get_config().project_root
    try:
        interceptor = OdgsInterceptor(project_root_path=root)
        result = interceptor.conformance_check(level=level)
        return json.dumps(result, indent=2, default=str)
    except ConformanceException as e:
        return json.dumps({
            "conformant": False,
            "level": e.level,
            "failures": e.failures,
            "error": str(e),
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": f"Conformance check failed: {e}"}, default=str)


# ── Pro Tools (require API key) ───────────────────────────────────


@mcp.tool()
def compile_regulation(
    regulation_text: str,
    regulation_name: str | None = None,
    provider: str | None = None,
) -> str:
    """Convert regulation text into ODGS rule JSON.

    Paste any statute, regulatory article, or SLA clause and get back
    validated ODGS rule objects ready for enforcement.

    Supports: EU AI Act, DORA, GDPR, CSRD, NIS2, Basel III, and any free-text regulation.

    Args:
        regulation_text: Raw regulation text to compile.
        regulation_name: Optional regulation identifier.
        provider: LLM provider — "ollama" (local), "google-genai", or "openai-compat".
    """
    gate_error = _check_tier("compile_regulation")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.compile import compile_regulation as _compile

    result = _compile(
        regulation_text=regulation_text,
        regulation_name=regulation_name,
        provider=provider,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def check_drift(
    definitions_dir: str,
    threshold_days: int = 90,
    provider: str | None = None,
) -> str:
    """Detect semantic drift in governance definitions.

    Scans legislative definitions for staleness, expired hashes,
    outdated regulatory references, and semantic inconsistencies.

    Args:
        definitions_dir: Path to the directory containing governance definitions.
        threshold_days: Days after which a definition is considered stale (default: 90).
        provider: LLM provider override.
    """
    gate_error = _check_tier("check_drift")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.drift import check_drift as _drift

    result = _drift(
        definitions_dir=definitions_dir,
        threshold_days=threshold_days,
        provider=provider,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def detect_conflicts(
    rules: list[dict[str, Any]],
    provider: str | None = None,
) -> str:
    """Find contradictions between governance rules.

    Cross-references rules from multiple regulatory sources to surface
    semantic conflicts, overlapping jurisdictions, and contradictions.

    Args:
        rules: List of ODGS rule objects to analyze for conflicts.
        provider: LLM provider override.
    """
    gate_error = _check_tier("detect_conflicts")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.conflicts import detect_conflicts as _conflicts

    result = _conflicts(rules=rules, provider=provider)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def narrate_audit(
    scert: dict[str, Any],
    audience: str = "executive",
    provider: str | None = None,
) -> str:
    """Convert an S-Cert into a human-readable narrative.

    Transforms cryptographic audit certificates into plain-language
    narratives tailored for the target audience.

    Args:
        scert: S-Cert JSON object from a validation run.
        audience: Target audience — "executive", "legal", "technical", or "auditor".
        provider: LLM provider override.
    """
    gate_error = _check_tier("narrate_audit")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.narrate import narrate_audit as _narrate

    result = _narrate(scert=scert, audience=audience, provider=provider)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def discover_bindings(
    catalog_metadata: dict[str, Any],
    metrics: list[dict[str, Any]] | None = None,
    provider: str | None = None,
) -> str:
    """Generate physical data mappings from catalog metadata.

    Given data catalog metadata (tables, columns, descriptions),
    auto-generates physical_data_map.json bindings to ODGS metrics.

    Args:
        catalog_metadata: Data catalog metadata with table/column info.
        metrics: Optional ODGS metric definitions to bind against.
        provider: LLM provider override.
    """
    gate_error = _check_tier("discover_bindings")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.discover import discover_bindings as _discover

    result = _discover(
        catalog_metadata=catalog_metadata,
        metrics=metrics,
        provider=provider,
    )
    return json.dumps(result, indent=2, default=str)


# ── Enterprise Tools (require API key) ────────────────────────────

@mcp.tool()
def harvest_sovereign_rules(
    source_text: str | None = None,
    source_url: str | None = None,
    harvester_type: str = "generic",
) -> str:
    """Extract sovereign rules from regulation using the Flint Bridge.

    Requires Enterprise tier and the `odgs-commercial` package.
    Automates the extraction of sovereign data rules from raw legal text
    or URLs and mints a Certified Regulation Pack.

    Args:
        source_text: Raw regulation text to harvest.
        source_url: URL to regulation source (alternative to text).
        harvester_type: Blueprint/harvester type (e.g., 'eu_ai_act', 'generic').
    """
    gate_error = _check_tier("harvest_sovereign_rules")
    if gate_error:
        return gate_error

    from odgs_mcp_server.tools.flint import harvest_sovereign_rules as _harvest
    
    result = _harvest(
        source_text=source_text,
        source_url=source_url,
        harvester_type=harvester_type,
    )
    return json.dumps(result, indent=2, default=str)



# ── Resources ─────────────────────────────────────────────────────


@mcp.resource("odgs://status")
def server_status() -> str:
    """Current server status, tier, and capabilities."""
    auth = _get_auth()
    cfg = _get_config()

    from odgs_mcp_server.auth import TOOL_TIERS, TIER_RANK

    accessible_tools = [
        tool for tool, tier in TOOL_TIERS.items()
        if TIER_RANK.get(auth.tier, 0) >= TIER_RANK.get(tier, 0)
    ]

    status = {
        "server": "ODGS Governance Server",
        "version": __version__,
        "tier": auth.tier,
        "project_root": cfg.project_root,
        "accessible_tools": sorted(accessible_tools),
        "total_tools": len(TOOL_TIERS),
        "upgrade_url": "https://platform.metricprovenance.com" if auth.tier == "community" else None,
    }
    return json.dumps(status, indent=2)


# ── CLI Entry Point ───────────────────────────────────────────────


def main():
    """CLI entry point for odgs-mcp-server."""
    parser = argparse.ArgumentParser(
        prog="odgs-mcp-server",
        description="ODGS Governance MCP Server — runtime enforcement for AI agents",
    )
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--project-root", "-p",
        default=None,
        help="Path to ODGS project root (default: $ODGS_PROJECT_ROOT or cwd)",
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="ODGS API key for Pro/Enterprise tier (default: $ODGS_API_KEY)",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"odgs-mcp-server {__version__}",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,  # MCP uses stdout for protocol; logs go to stderr
    )

    # Initialize global config
    global _config, _auth
    _config = ServerConfig(
        transport=args.transport,
        project_root=args.project_root or ServerConfig().project_root,
        api_key=args.api_key or ServerConfig().api_key,
    )
    _config.ensure_cache_dir()

    _auth = AuthGate(
        api_key=_config.api_key,
        registry_url=_config.registry_url,
        cache_dir=_config.cache_dir,
    )

    logger.info(
        "Starting ODGS MCP Server v%s (tier=%s, transport=%s, project=%s)",
        __version__, _auth.tier, args.transport, _config.project_root,
    )

    # Run the server
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
