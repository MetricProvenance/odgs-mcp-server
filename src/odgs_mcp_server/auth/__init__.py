"""
Auth gate — controls tool access based on API key tier.

Tiers:
- community (no key): validate_payload, list_packs, governance_score, conformance_check
- pro (API key): + compile_regulation, check_drift, detect_conflicts, narrate_audit, discover_bindings
- enterprise (API key): + sync_catalog
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Tool → minimum tier required
TOOL_TIERS: dict[str, str] = {
    # Community (free)
    "validate_payload": "community",
    "list_packs": "community",
    "governance_score": "community",
    "conformance_check": "community",
    # Pro
    "compile_regulation": "pro",
    "check_drift": "pro",
    "detect_conflicts": "pro",
    "narrate_audit": "pro",
    "discover_bindings": "pro",
    # Enterprise
    "sync_catalog": "enterprise",
    "harvest_sovereign_rules": "enterprise",
}

TIER_RANK = {"community": 0, "pro": 1, "enterprise": 2}


class AuthGate:
    """Validates API keys and controls tool access by tier."""

    def __init__(self, api_key: str | None = None, registry_url: str = "", cache_dir: str = ""):
        self.api_key = api_key
        self.registry_url = registry_url
        self.cache_dir = cache_dir
        self._tier: str | None = None
        self._tier_cached_at: float = 0
        self._cache_ttl = 86400  # 24 hours

    @property
    def tier(self) -> str:
        """Resolve the current tier. Caches for 24h after first validation."""
        if self._tier and (time.time() - self._tier_cached_at) < self._cache_ttl:
            return self._tier

        if not self.api_key:
            self._tier = "community"
            self._tier_cached_at = time.time()
            return self._tier

        # Try cached tier from disk first
        cached = self._read_cached_tier()
        if cached:
            self._tier = cached
            self._tier_cached_at = time.time()
            return self._tier

        # Validate against registry
        self._tier = self._validate_key_remote()
        self._tier_cached_at = time.time()
        self._write_cached_tier(self._tier)
        return self._tier

    def check_access(self, tool_name: str) -> bool:
        """Check if the current tier can access the given tool."""
        required_tier = TOOL_TIERS.get(tool_name, "enterprise")
        return TIER_RANK.get(self.tier, 0) >= TIER_RANK.get(required_tier, 0)

    def upgrade_message(self, tool_name: str) -> str:
        """Return a user-friendly upgrade prompt."""
        required = TOOL_TIERS.get(tool_name, "enterprise")
        return (
            f"🔒 `{tool_name}` requires a Certified Pack licence "
            f"(ODGS {required.title()} tier).\n\n"
            f"Your current tier: **{self.tier}**\n\n"
            f"Certified Packs are issued through verified "
            f"Metric Provenance partners.\n\n"
            f"→ Technical brief for your governance lead: "
            f"https://www.metricprovenance.com/brief\n"
            f"→ Partner enquiries: partner@metricprovenance.com\n\n"
            f"If your organisation already has a licence, set your key:\n"
            f"  export ODGS_API_KEY=sk-odgs-...\n"
            f"  # or in your MCP client config"
        )

    def _validate_key_remote(self) -> str:
        """Validate API key against the ODGS registry. Returns tier string."""
        if not self.registry_url or not self.api_key:
            return "community"

        try:
            import httpx

            # Always ensure trailing slash is stripped from registry_url
            url = self.registry_url.rstrip('/')
            
            resp = httpx.post(
                f"{url}/api/v1/validate-key",
                json={"api_key": self.api_key},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                tier = data.get("tier", "community")
                logger.info("API key validated: tier=%s", tier)
                return tier
            else:
                logger.warning("Key validation failed: HTTP %s", resp.status_code)
                return "community"
        except Exception as e:
            logger.warning("Key validation failed (network): %s — falling back to community", e)
            return "community"

    def _cache_path(self) -> Path | None:
        """Path to the tier cache file."""
        if not self.cache_dir:
            return None
        p = Path(self.cache_dir) / ".tier_cache.json"
        return p

    def _read_cached_tier(self) -> str | None:
        """Read cached tier from disk if fresh enough."""
        path = self._cache_path()
        if not path or not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            cached_at = data.get("cached_at", 0)
            if (time.time() - cached_at) < self._cache_ttl:
                return data.get("tier")
        except Exception:
            pass
        return None

    def _write_cached_tier(self, tier: str) -> None:
        """Persist tier to disk cache."""
        path = self._cache_path()
        if not path:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "tier": tier,
                "cached_at": time.time(),
                "api_key_prefix": self.api_key[:8] + "..." if self.api_key else None,
            }))
        except Exception as e:
            logger.debug("Failed to cache tier: %s", e)
