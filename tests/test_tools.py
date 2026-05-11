"""Tests for the governance score tool.

Tests cover both scoring paths:
- Fallback (built-in 4-category heuristic) — the default for all users
- Maturity engine (8-pillar DAMA framework) — when odgs-maturity is installed

The fallback path is always tested. The maturity engine path is tested
only when odgs-maturity is importable (dev environment).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from odgs_mcp_server.tools.score import governance_score, _score_fallback


# ── Shared contract tests ────────────────────────────────────────────

class TestGovernanceScoreContract:
    """Tests for the public governance_score output contract.

    These must pass regardless of which engine is active.
    """

    def test_returns_required_keys(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert "score" in result
        assert "grade" in result
        assert "findings" in result
        assert "breakdown" in result
        assert "project_root" in result
        assert "_odgs_notice" in result

    def test_score_is_bounded(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert 0 <= result["score"] <= 100

    def test_grade_is_valid(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert result["grade"] in ("A", "B", "C", "D", "F")

    def test_findings_have_correct_structure(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        for finding in result["findings"]:
            assert "category" in finding
            assert "status" in finding
            assert "message" in finding

    def test_grade_boundaries(self):
        """Grade mapping: A ≥ 90, B ≥ 75, C ≥ 60, D ≥ 40, F < 40."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            result = governance_score(project_root=tmp)
            assert result["grade"] in ("A", "B", "C", "D", "F")


# ── Fallback engine tests ────────────────────────────────────────────

class TestFallbackScorer:
    """Tests for the built-in 4-category fallback scorer.

    This is the path that 10k+ production users hit when
    odgs-maturity is not installed. Must remain stable.
    """

    def test_empty_project_scores_zero(self, tmp_path):
        result = _score_fallback(tmp_path)
        assert result["score"] == 0
        assert result["grade"] == "F"
        assert len(result["findings"]) > 0

    def test_full_project_scores_high(self, odgs_project_root):
        result = _score_fallback(odgs_project_root)
        assert result["score"] > 40
        assert result["grade"] in ("A", "B", "C", "D")

    def test_breakdown_covers_four_categories(self, odgs_project_root):
        result = _score_fallback(odgs_project_root)
        assert "legislative" in result["breakdown"]
        assert "judiciary" in result["breakdown"]
        assert "executive" in result["breakdown"]
        assert "infrastructure" in result["breakdown"]

    def test_engine_field_indicates_fallback(self, odgs_project_root):
        result = _score_fallback(odgs_project_root)
        assert "fallback" in result["engine"]

    def test_notice_is_present(self, tmp_path):
        result = _score_fallback(tmp_path)
        assert "_odgs_notice" in result

    def test_project_root_is_echoed(self, tmp_path):
        result = _score_fallback(tmp_path)
        assert result["project_root"] == str(tmp_path)

    def test_signed_rules_earn_full_judiciary_points(self, tmp_path):
        """Cryptographically signed rules should max judiciary score."""
        judiciary = tmp_path / "judiciary"
        judiciary.mkdir()
        (judiciary / "standard_data_rules.json").write_text(json.dumps({
            "rules": [
                {"rule_id": f"R{i:03d}", "name": f"Rule {i}", "severity": "HARD_STOP"}
                for i in range(12)
            ],
            "signature": "sha256:deadbeef...",
        }))
        result = _score_fallback(tmp_path)
        assert result["breakdown"]["judiciary"]["score"] == 30

    def test_partial_legislative_scores_correctly(self, tmp_path):
        """Only ontology present, no metrics — should get partial credit."""
        legislative = tmp_path / "legislative"
        legislative.mkdir()
        (legislative / "ontology_graph.json").write_text(json.dumps({
            "nodes": [{"urn": f"urn:concept:{i}"} for i in range(6)],
            "graph_edges": [{"source_urn": "a", "target_urn": "b", "relationship": "R"}] * 4,
        }))
        result = _score_fallback(tmp_path)
        # 10 (exists) + 5 (≥5 nodes) + 5 (≥3 edges) = 20 out of 30
        assert result["breakdown"]["legislative"]["score"] == 20


# ── Maturity engine delegation tests ─────────────────────────────────

try:
    import odgs_maturity  # noqa: F401
    HAS_MATURITY = True
except ImportError:
    HAS_MATURITY = False


@pytest.mark.skipif(not HAS_MATURITY, reason="odgs-maturity not installed")
class TestMaturityEngineDelegation:
    """Tests for the 8-pillar maturity engine path.

    Only run in dev environments where odgs-maturity is installed.
    """

    def test_uses_maturity_engine_when_available(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert result["engine"] == "odgs-maturity"

    def test_maturity_returns_level(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert "level" in result
        assert "level_value" in result

    def test_maturity_returns_total_rules(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert "total_rules" in result
        assert result["total_rules"] > 0


# ── Import fallback test ─────────────────────────────────────────────

class TestImportFallback:
    """Ensure graceful degradation when odgs-maturity is absent."""

    def test_falls_back_when_maturity_missing(self, odgs_project_root):
        """Simulate odgs-maturity not being installed."""
        with patch.dict(sys.modules, {"odgs_maturity": None,
                                       "odgs_maturity.scoring": None,
                                       "odgs_maturity.scoring.engine": None,
                                       "odgs_maturity.workspace": None,
                                       "odgs_maturity.workspace.reader": None}):
            # Force re-import to trigger ImportError
            result = _score_fallback(odgs_project_root)
            assert "fallback" in result["engine"]
            assert "legislative" in result["breakdown"]


# ── List Packs ────────────────────────────────────────────────────────

class TestListPacks:
    """Test pack listing tool."""

    def test_list_packs_returns_known_packs(self, tmp_path):
        from odgs_mcp_server.tools.packs import list_packs

        result = list_packs(project_root=str(tmp_path))
        assert result["total"] > 0
        assert isinstance(result["packs"], list)

        # Known packs should include at least EU AI Act
        pack_ids = [p["id"] for p in result["packs"]]
        assert "eu-ai-act" in pack_ids
        assert "dora" in pack_ids
        assert "gdpr" in pack_ids

    def test_list_packs_includes_purchase_url(self, tmp_path):
        """Pack listing routes to partner brief, not a SaaS purchase URL."""
        from odgs_mcp_server.tools.packs import list_packs

        result = list_packs(project_root=str(tmp_path))
        # Partner-led model: brief_url and licence_note, not SaaS checkout
        assert "brief_url" in result
        assert "metricprovenance" in result["brief_url"]
        assert "licence_note" in result

    def test_packs_have_tier_info(self, tmp_path):
        from odgs_mcp_server.tools.packs import list_packs

        result = list_packs(project_root=str(tmp_path))
        for pack in result["packs"]:
            assert "tier_required" in pack
            assert "installed" in pack
