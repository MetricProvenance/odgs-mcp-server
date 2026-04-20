"""
governance_score — Score a dataset's governance maturity.

Analyzes the ODGS project configuration to produce a 0-100 governance
maturity score with regulation-specific findings.

Tier: Community (free)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from odgs_mcp_server.tools._notice import certification_notice

logger = logging.getLogger(__name__)


def governance_score(
    project_root: str,
) -> dict[str, Any]:
    """
    Compute a governance maturity score for an ODGS project.

    Analyzes the completeness and quality of governance definitions,
    rules, bindings, and cryptographic signing.

    Args:
        project_root: Path to the ODGS project root.

    Returns:
        Dict with:
        - score (int): 0-100 governance maturity score.
        - grade (str): Letter grade (A-F).
        - findings (list): Specific findings with recommendations.
        - breakdown (dict): Score breakdown by category.
    """
    root = Path(project_root)
    findings: list[dict[str, str]] = []
    breakdown: dict[str, dict[str, Any]] = {}

    # ── 1. Legislative Plane (30 points) ──────────────────────────
    legislative_score = 0
    legislative_max = 30

    ontology = root / "legislative" / "ontology_graph.json"
    if ontology.exists():
        legislative_score += 10
        try:
            data = json.loads(ontology.read_text())
            node_count = len(data.get("nodes", []))
            edge_count = len(data.get("graph_edges", data.get("edges", [])))
            if node_count >= 5:
                legislative_score += 5
            if edge_count >= 3:
                legislative_score += 5
            findings.append({
                "category": "Legislative",
                "status": "✅",
                "message": f"Ontology graph loaded: {node_count} nodes, {edge_count} edges",
            })
        except Exception:
            findings.append({
                "category": "Legislative",
                "status": "⚠️",
                "message": "Ontology graph exists but could not be parsed",
            })
    else:
        findings.append({
            "category": "Legislative",
            "status": "❌",
            "message": "Missing legislative/ontology_graph.json — no governance ontology defined",
            "recommendation": "Create an ontology graph with governance concepts and relationships",
        })

    metrics = root / "legislative" / "standard_metrics.json"
    if metrics.exists():
        legislative_score += 10
        findings.append({"category": "Legislative", "status": "✅", "message": "Standard metrics defined"})
    else:
        findings.append({
            "category": "Legislative", "status": "⚠️",
            "message": "No standard_metrics.json — quality metrics not formalized",
        })

    breakdown["legislative"] = {"score": legislative_score, "max": legislative_max}

    # ── 2. Judiciary Plane (30 points) ────────────────────────────
    judiciary_score = 0
    judiciary_max = 30

    rules_file = root / "judiciary" / "standard_data_rules.json"
    if rules_file.exists():
        judiciary_score += 10
        try:
            data = json.loads(rules_file.read_text())
            rules_list = data.get("rules", []) if isinstance(data, dict) else data
            rule_count = len(rules_list) if isinstance(rules_list, list) else 0

            if rule_count >= 3:
                judiciary_score += 5
            if rule_count >= 10:
                judiciary_score += 5

            # Check for cryptographic signing
            has_signature = isinstance(data, dict) and "signature" in data
            if has_signature:
                judiciary_score += 10
                findings.append({"category": "Judiciary", "status": "✅", "message": f"{rule_count} rules defined, cryptographically signed"})
            else:
                findings.append({"category": "Judiciary", "status": "⚠️", "message": f"{rule_count} rules defined but NOT cryptographically signed"})

        except Exception:
            findings.append({"category": "Judiciary", "status": "⚠️", "message": "Rules file exists but could not be parsed"})
    else:
        findings.append({
            "category": "Judiciary", "status": "❌",
            "message": "Missing judiciary/standard_data_rules.json — no governance rules defined",
            "recommendation": "Define data quality and compliance rules",
        })

    breakdown["judiciary"] = {"score": judiciary_score, "max": judiciary_max}

    # ── 3. Executive Plane (25 points) ────────────────────────────
    executive_score = 0
    executive_max = 25

    bindings = root / "executive" / "context_bindings.json"
    if bindings.exists():
        executive_score += 10
        findings.append({"category": "Executive", "status": "✅", "message": "Context bindings configured"})
    else:
        findings.append({
            "category": "Executive", "status": "❌",
            "message": "Missing context_bindings.json — rules are not bound to processes",
        })

    physical_map = root / "executive" / "physical_data_map.json"
    if physical_map.exists():
        executive_score += 10
        findings.append({"category": "Executive", "status": "✅", "message": "Physical data mappings defined"})
    else:
        findings.append({
            "category": "Executive", "status": "⚠️",
            "message": "No physical_data_map.json — data source bindings not configured",
        })

    bpm = root / "executive" / "business_process_maps.json"
    if bpm.exists():
        executive_score += 5
        findings.append({"category": "Executive", "status": "✅", "message": "Business process maps defined"})

    breakdown["executive"] = {"score": executive_score, "max": executive_max}

    # ── 4. Infrastructure (15 points) ─────────────────────────────
    infra_score = 0
    infra_max = 15

    authorities = root / "schemas" / "authorities.json"
    if not authorities.exists():
        authorities = root / "authorities.json"
    if authorities.exists():
        infra_score += 10
        findings.append({"category": "Infrastructure", "status": "✅", "message": "Cryptographic authorities configured (JWKS)"})
    else:
        findings.append({
            "category": "Infrastructure", "status": "⚠️",
            "message": "No authorities.json — S-Certs will be unsigned",
            "recommendation": "Configure JWKS authorities for cryptographic pack signing",
        })

    schemas_dir = root / "schemas" / "validation"
    if schemas_dir.exists() and any(schemas_dir.glob("*.json")):
        infra_score += 5
        findings.append({"category": "Infrastructure", "status": "✅", "message": "JSON Schema validation files present"})

    breakdown["infrastructure"] = {"score": infra_score, "max": infra_max}

    # ── Final Score ───────────────────────────────────────────────
    total_score = legislative_score + judiciary_score + executive_score + infra_score
    total_max = legislative_max + judiciary_max + executive_max + infra_max

    # Normalize to 0-100
    score = round((total_score / total_max) * 100) if total_max > 0 else 0

    # Grade
    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": score,
        "grade": grade,
        "findings": findings,
        "breakdown": breakdown,
        "project_root": str(root),
        "_odgs_notice": certification_notice(score=score),
    }
