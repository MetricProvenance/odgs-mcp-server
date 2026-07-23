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
        assert gate.check_access("harvest_sovereign_rules") is False

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
        msg = gate.upgrade_message("harvest_sovereign_rules")
        assert "community" in msg
        # Should mention partner route not SaaS pricing
        assert "partner" in msg.lower() or "partner@metricprovenance.com" in msg


class TestLockoutRegression:
    """Regression tests for the 24h community-lockout bug.

    A failed or unreachable key validation used to be persisted to the disk
    cache as 'community', locking licensed users out for the full 24h TTL.
    Only successful (HTTP 200) validations may be written to disk.
    """

    def test_network_error_result_is_not_cached_to_disk(self, tmp_path, monkeypatch):
        import httpx

        def boom(*args, **kwargs):
            raise httpx.ConnectError("registry unreachable")

        monkeypatch.setattr(httpx, "post", boom)
        gate = AuthGate(
            api_key="sk-odgs-test",
            registry_url="https://registry.example.com",
            cache_dir=str(tmp_path),
        )
        assert gate.tier == "community"  # graceful fallback for this process
        assert not (tmp_path / ".tier_cache.json").exists()

    def test_http_error_result_is_not_cached_to_disk(self, tmp_path, monkeypatch):
        import httpx

        class FakeResponse:
            status_code = 503

        monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse())
        gate = AuthGate(
            api_key="sk-odgs-test",
            registry_url="https://registry.example.com",
            cache_dir=str(tmp_path),
        )
        assert gate.tier == "community"
        assert not (tmp_path / ".tier_cache.json").exists()

    def test_successful_validation_is_cached_and_recovers_after_outage(self, tmp_path, monkeypatch):
        import httpx

        # 1. Outage: falls back to community, nothing persisted
        def boom(*args, **kwargs):
            raise httpx.ConnectError("registry unreachable")

        monkeypatch.setattr(httpx, "post", boom)
        gate = AuthGate(
            api_key="sk-odgs-test",
            registry_url="https://registry.example.com",
            cache_dir=str(tmp_path),
        )
        assert gate.tier == "community"

        # 2. Registry back up: a fresh gate must validate as pro immediately
        #    (before the fix, the poisoned disk cache pinned it to community)
        class FakeResponse:
            status_code = 200

            @staticmethod
            def json():
                return {"tier": "pro"}

        monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse())
        gate2 = AuthGate(
            api_key="sk-odgs-test",
            registry_url="https://registry.example.com",
            cache_dir=str(tmp_path),
        )
        assert gate2.tier == "pro"

        # 3. Successful result IS persisted for the 24h fast path
        cached = json.loads((tmp_path / ".tier_cache.json").read_text())
        assert cached["tier"] == "pro"


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


class TestTierCacheKeyBinding:
    """Regression tests: a cached tier must never leak to a different API key.

    Before the fix, `_read_cached_tier` only checked the cache's freshness
    (24h TTL), never whether it was written for the key currently presented.
    Any non-empty key — garbage, expired, revoked, a typo — inherited the
    last successfully-validated tier on that machine for up to 24h, because
    only the explicit "no key at all" path bypassed the disk cache. This
    silently granted pro/enterprise access to the wrong caller.
    """

    def test_garbage_key_does_not_inherit_a_different_keys_cached_pro_tier(self, tmp_path):
        real_key_gate = AuthGate(api_key="sk-odgs-real-pro-key", cache_dir=str(tmp_path))
        real_key_gate._write_cached_tier("pro")

        garbage_gate = AuthGate(api_key="totally-different-garbage", cache_dir=str(tmp_path))
        assert garbage_gate._read_cached_tier() is None

    def test_same_key_still_hits_the_cache(self, tmp_path):
        gate = AuthGate(api_key="sk-odgs-real-pro-key", cache_dir=str(tmp_path))
        gate._write_cached_tier("pro")

        gate2 = AuthGate(api_key="sk-odgs-real-pro-key", cache_dir=str(tmp_path))
        assert gate2._read_cached_tier() == "pro"

    def test_empty_key_does_not_inherit_cached_pro_tier(self, tmp_path):
        real_key_gate = AuthGate(api_key="sk-odgs-real-pro-key", cache_dir=str(tmp_path))
        real_key_gate._write_cached_tier("pro")

        no_key_gate = AuthGate(api_key=None, cache_dir=str(tmp_path))
        assert no_key_gate._read_cached_tier() is None
        assert no_key_gate.tier == "community"

    def test_cache_written_by_no_key_is_not_read_by_a_real_key(self, tmp_path):
        no_key_gate = AuthGate(api_key=None, cache_dir=str(tmp_path))
        no_key_gate._write_cached_tier("community")

        real_key_gate = AuthGate(api_key="sk-odgs-real-pro-key", cache_dir=str(tmp_path))
        assert real_key_gate._read_cached_tier() is None
