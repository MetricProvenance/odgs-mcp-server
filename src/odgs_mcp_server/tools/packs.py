"""
list_packs — List available Certified Packs.

Scans the ODGS project root and cache directory for installed
Sovereign Definition packs (regulation-specific rule bundles).

Tier: Community (free)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Known certified packs (from odgs-commercial)
KNOWN_PACKS = [
    {"id": "eu-ai-act", "name": "EU AI Act", "regulation": "EU AI Act (2024/1689)", "status": "certified"},
    {"id": "dora", "name": "DORA", "regulation": "Digital Operational Resilience Act", "status": "certified"},
    {"id": "csrd", "name": "CSRD", "regulation": "Corporate Sustainability Reporting Directive", "status": "certified"},
    {"id": "gdpr", "name": "GDPR", "regulation": "General Data Protection Regulation", "status": "certified"},
    {"id": "nis2", "name": "NIS2", "regulation": "Network and Information Security Directive", "status": "certified"},
    {"id": "basel-iii", "name": "Basel III", "regulation": "Basel III Banking Regulation", "status": "certified"},
    {"id": "solvency-ii", "name": "Solvency II", "regulation": "Insurance Solvency Directive", "status": "certified"},
    {"id": "mifid-ii", "name": "MiFID II", "regulation": "Markets in Financial Instruments Directive", "status": "certified"},
    {"id": "ifrs", "name": "IFRS", "regulation": "International Financial Reporting Standards", "status": "certified"},
    {"id": "bcbs-239", "name": "BCBS 239", "regulation": "Basel Committee Risk Data Aggregation", "status": "certified"},
    {"id": "soc2", "name": "SOC 2", "regulation": "Service Organization Control 2", "status": "certified"},
    {"id": "iso-27001", "name": "ISO 27001", "regulation": "Information Security Management", "status": "certified"},
    {"id": "hipaa", "name": "HIPAA", "regulation": "Health Insurance Portability and Accountability Act", "status": "certified"},
    {"id": "pci-dss", "name": "PCI DSS", "regulation": "Payment Card Industry Data Security Standard", "status": "certified"},
    {"id": "aml-6", "name": "AML-6", "regulation": "6th Anti-Money Laundering Directive", "status": "certified"},
]


def list_packs(
    project_root: str,
    cache_dir: str | None = None,
) -> dict[str, Any]:
    """
    List available ODGS Certified Packs.

    Checks local project directory and cache for installed packs,
    and lists all known packs from the registry.

    Args:
        project_root: Path to the ODGS project root.
        cache_dir: Path to the local pack cache directory.

    Returns:
        Dict with:
        - packs (list): Available packs with id, name, regulation, installed status.
        - total (int): Total number of known packs.
        - installed (int): Number locally installed/available.
    """
    installed_ids = set()

    # Check project root for judiciary/ directories with rules
    judiciary_path = Path(project_root) / "judiciary"
    if judiciary_path.exists():
        rules_file = judiciary_path / "standard_data_rules.json"
        if rules_file.exists():
            try:
                data = json.loads(rules_file.read_text())
                # Extract pack metadata if present
                if isinstance(data, dict):
                    pack_id = data.get("pack_id") or data.get("regulation_id")
                    if pack_id:
                        installed_ids.add(pack_id)
                    # Check rules for regulation references
                    for rule in data.get("rules", []):
                        reg = rule.get("regulation")
                        if reg:
                            installed_ids.add(reg.lower().replace(" ", "-"))
            except Exception as e:
                logger.debug("Failed to read rules file: %s", e)

    # Check cache directory for downloaded packs
    if cache_dir:
        cache_path = Path(cache_dir) / "packs"
        if cache_path.exists():
            for pack_dir in cache_path.iterdir():
                if pack_dir.is_dir():
                    installed_ids.add(pack_dir.name)

    # Build response
    packs = []
    processed_ids = set()
    
    for pack in KNOWN_PACKS:
        packs.append({
            **pack,
            "installed": pack["id"] in installed_ids,
            "tier_required": "pro",
        })
        processed_ids.add(pack["id"])
        
    # Add any installed packs that are not in KNOWN_PACKS (e.g. test/custom packs)
    for pack_id in installed_ids:
        if pack_id not in processed_ids:
            packs.append({
                "id": pack_id,
                "name": pack_id.replace("-", " ").title(),
                "regulation": "Custom/Sovereign Pack",
                "status": "custom",
                "installed": True,
                "tier_required": "community"
            })

    return {
        "packs": packs,
        "total": len(packs),
        "installed": sum(1 for p in packs if p["installed"]),
        "access_url": "https://metricprovenance.com/pricing",
        "licence_note": "Certified Packs are issued via Metric Provenance partners. To request access, visit metricprovenance.com/pricing",
    }


def download_pack(
    pack_id: str,
    registry_url: str,
    cache_dir: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Download a certified regulation pack from the registry.

    Args:
        pack_id: The ID of the pack to download (e.g., "eu-ai-act").
        registry_url: URL of the ODGS registry.
        cache_dir: Directory to store downloaded packs.
        api_key: API key for authentication.

    Returns:
        Dict indicating success or failure.
    """
    if not cache_dir:
        return {"success": False, "error": "No cache directory configured."}
        
    if not registry_url:
        return {"success": False, "error": "No registry URL configured."}

    import httpx
    
    url = registry_url.rstrip('/')
    
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        logger.info("Downloading pack %s from %s", pack_id, url)
        resp = httpx.get(
            f"{url}/api/v1/download-pack/{pack_id}",
            headers=headers,
            timeout=15,
        )
        
        if resp.status_code == 200:
            pack_data = resp.json()

            # Save to cache
            cache_path = Path(cache_dir) / "packs" / pack_id
            cache_path.mkdir(parents=True, exist_ok=True)

            # Raw bundle (manifest + signature) for provenance/verification
            pack_file = cache_path / "rules.json"
            pack_file.write_text(json.dumps(pack_data, indent=2))

            # v0.3.0: materialize an ENGINE-BOOTABLE project layout so the
            # purchased rules are actually usable — previously the bundle was
            # cached but never readable by the validation engine.
            engine_ready = False
            if isinstance(pack_data, dict) and pack_data.get("content") == "bundle":
                rules = pack_data.get("rules") or []
                if rules:
                    judiciary = cache_path / "judiciary"
                    judiciary.mkdir(parents=True, exist_ok=True)
                    (judiciary / "standard_data_rules.json").write_text(
                        json.dumps(rules, indent=2)
                    )
                    engine_ready = True
                for relpath, content in (pack_data.get("sovereign") or {}).items():
                    # Guard against path traversal from a hostile bundle.
                    # A string-prefix check here is bypassable (e.g. "../sovereign-evil/x"
                    # resolves to a sibling dir that still startswith "...sovereign") —
                    # is_relative_to() checks actual path containment, not string prefix.
                    dest = (cache_path / "sovereign" / relpath).resolve()
                    if dest.is_relative_to((cache_path / "sovereign").resolve()):
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(
                            content if isinstance(content, str) else json.dumps(content, indent=2)
                        )
                manifest = pack_data.get("manifest")
                if manifest:
                    (cache_path / "manifest.json").write_text(
                        manifest if isinstance(manifest, str) else json.dumps(manifest, indent=2)
                    )

            if engine_ready:
                return {
                    "success": True,
                    "pack_id": pack_id,
                    "engine_ready": True,
                    "project_root": str(cache_path),
                    "message": (
                        f"Pack {pack_id} installed to {cache_path} in engine-ready layout. "
                        f"Validate against it by passing project_root='{cache_path}' to "
                        f"validate_payload, or set ODGS_PROJECT_ROOT to that path "
                        f"(or copy judiciary/ and sovereign/ into your own project). "
                        f"Note: the pack ships the rules themselves (judiciary/, sovereign/); "
                        f"validate_payload also needs your own legislative/ontology_graph.json "
                        f"and executive/context_bindings.json to bind these rules to your "
                        f"process URNs — those are project-specific and not part of the pack. "
                        f"A minimal ontology_graph.json is just {{\"graph_edges\": []}}; "
                        f"context_bindings.json maps a process_urn to the rule urns it enforces."
                    ),
                }
            return {
                "success": True,
                "pack_id": pack_id,
                "engine_ready": False,
                "message": f"Downloaded pack metadata for {pack_id} to {cache_path} (no rule bundle in response).",
            }
        elif resp.status_code == 404:
            return {"success": False, "error": f"Pack {pack_id} not found or not entitled."}
        else:
            return {"success": False, "error": f"Registry returned HTTP {resp.status_code}"}
    except Exception as e:
        logger.error("Failed to download pack %s: %s", pack_id, e)
        return {"success": False, "error": f"Network error: {str(e)}"}

