"""
ODGS MCP Server configuration.

Configuration is loaded from environment variables and CLI arguments.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ServerConfig:
    """Server configuration resolved from environment + CLI args."""

    # Transport: "stdio" (default, local) or "http" (enterprise)
    transport: str = "stdio"

    # ODGS project root — where the governance definitions live.
    # Falls back to $ODGS_PROJECT_ROOT, then current working directory.
    project_root: str = field(default_factory=lambda: os.environ.get(
        "ODGS_PROJECT_ROOT", os.getcwd()
    ))

    # API key for Pro/Enterprise tier access.
    # Read from $ODGS_API_KEY or --api-key CLI arg.
    api_key: str | None = field(default_factory=lambda: os.environ.get("ODGS_API_KEY"))

    # Registry URL for API key validation + pack downloads.
    registry_url: str = field(default_factory=lambda: os.environ.get(
        "ODGS_REGISTRY_URL", "https://registry.metricprovenance.com"
    ))

    # Path to cached packs (downloaded on first use for Pro tier).
    cache_dir: str = field(default_factory=lambda: os.environ.get(
        "ODGS_CACHE_DIR",
        str(Path.home() / ".odgs" / "cache")
    ))

    # HTTP transport settings (only used when transport="http")
    http_host: str = "0.0.0.0"
    http_port: int = 8080

    @classmethod
    def from_env(cls) -> ServerConfig:
        """Create config from environment variables."""
        return cls()

    def ensure_cache_dir(self) -> Path:
        """Create cache directory if it doesn't exist."""
        p = Path(self.cache_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p
