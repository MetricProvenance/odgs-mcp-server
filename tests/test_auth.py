"""Tests for the auth gate module."""

from __future__ import annotations

import json
import time
from pathlib import Path

from odgs_mcp_server.auth import AuthGate, TOOL_TIERS, TIER_RANK


class TestTierResolution:
    """Test tier resolution from API key."""

    def test_no_key_returns_community(self):
        gate = AuthGate(api_key=None)
        assert gate.tier == "community"

    def test_empty_key_returns_community(self):
        gate = AuthGate(api_key="")
        assert gate.tier == "community"

    def test_tier_is_cached_in_memory(self):
        gate = AuthGate(api_key=None)
        _ = gate.tier
        # Second access should use cache
        assert gate._tier_cached_at > 0
        assert gate.tier == "community"


class TestAccessControl:
    """Test tool access by tier."""

    def test_community_can_access_free_tools(self):
        gate = AuthGate(api_key=None)
        assert gate.check_access("validate_payload") is True
        assert gate.check_access("list_packs") is True
        assert gate.check_access("governance_score") is True
        assert gate.check_access("conformance_check") is True

    def test_community_cannot_access_pro_tools(self):
        gate = AuthGate(api_key=None)
        assert gate.check_access("compile_regulation") is False
        assert gate.check_access("check_drift") is False
        assert gate.check_access("detect_conflicts") is False
        assert gate.check_access("narrate_audit") is False
        assert gate.check_access("discover_bindings") is False

    def test_community_cannot_access_enterprise_tools(self):
        gate = AuthGate(api_key=None)
        assert gate.check_access("sync_catalog") is False

    def test_unknown_tool_requires_enterprise(self):
        gate = AuthGate(api_key=None)
        assert gate.check_access("unknown_future_tool") is False

    def test_all_tools_have_tiers(self):
        """Every tool must have a tier assignment."""
        for tool, tier in TOOL_TIERS.items():
            assert tier in TIER_RANK, f"Tool '{tool}' has unknown tier '{tier}'"


class TestUpgradeMessage:
    """Test upgrade messaging."""

    def test_upgrade_message_includes_tool_name(self):
        gate = AuthGate(api_key=None)
        msg = gate.upgrade_message("compile_regulation")
        assert "compile_regulation" in msg
        assert "Pro" in msg
        # Routes to partner brief + email enquiry (not SaaS checkout)
        assert "metricprovenance.com" in msg

    def test_upgrade_message_shows_current_tier(self):
        gate = AuthGate(api_key=None)
        msg = gate.upgrade_message("sync_catalog")
        assert "community" in msg
        # Should mention partner route not SaaS pricing
        assert "partner" in msg.lower() or "partner@metricprovenance.com" in msg


class TestDiskCache:
    """Test tier caching to disk."""

    def test_write_and_read_cached_tier(self, tmp_path):
        gate = AuthGate(api_key=None, cache_dir=str(tmp_path))
        gate._write_cached_tier("pro")

        cache_file = tmp_path / ".tier_cache.json"
        assert cache_file.exists()

        data = json.loads(cache_file.read_text())
        assert data["tier"] == "pro"

    def test_read_cached_tier_returns_value(self, tmp_path):
        gate = AuthGate(api_key=None, cache_dir=str(tmp_path))
        gate._write_cached_tier("enterprise")

        result = gate._read_cached_tier()
        assert result == "enterprise"

    def test_expired_cache_returns_none(self, tmp_path):
        gate = AuthGate(api_key=None, cache_dir=str(tmp_path))
        gate._cache_ttl = 0  # Expire immediately

        gate._write_cached_tier("pro")
        time.sleep(0.01)

        result = gate._read_cached_tier()
        assert result is None

    def test_no_cache_dir_gracefully_noop(self):
        gate = AuthGate(api_key=None, cache_dir="")
        gate._write_cached_tier("pro")  # Should not raise
        assert gate._read_cached_tier() is None
