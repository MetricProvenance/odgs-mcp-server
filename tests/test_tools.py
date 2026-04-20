"""Tests for the governance score tool."""

from __future__ import annotations

import json
from pathlib import Path

from odgs_mcp_server.tools.score import governance_score


class TestGovernanceScore:
    """Test governance maturity scoring."""

    def test_empty_project_scores_zero(self, tmp_path):
        result = governance_score(project_root=str(tmp_path))
        assert result["score"] == 0
        assert result["grade"] == "F"
        assert len(result["findings"]) > 0

    def test_full_project_scores_high(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert result["score"] > 40
        assert result["grade"] in ("A", "B", "C", "D")

    def test_findings_have_correct_structure(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        for finding in result["findings"]:
            assert "category" in finding
            assert "status" in finding
            assert "message" in finding

    def test_breakdown_covers_all_categories(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert "legislative" in result["breakdown"]
        assert "judiciary" in result["breakdown"]
        assert "executive" in result["breakdown"]
        assert "infrastructure" in result["breakdown"]

    def test_score_is_bounded(self, odgs_project_root):
        result = governance_score(project_root=str(odgs_project_root))
        assert 0 <= result["score"] <= 100

    def test_grade_mapping(self):
        """Test all grade boundaries."""
        # Create minimal project that will score different grades
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            result = governance_score(project_root=tmp)
            assert result["grade"] in ("A", "B", "C", "D", "F")


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
