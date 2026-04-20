"""Tests for the server config module."""

from __future__ import annotations

import os
from pathlib import Path

from odgs_mcp_server.config import ServerConfig


class TestServerConfig:
    """Test configuration resolution."""

    def test_default_config(self):
        config = ServerConfig()
        assert config.transport == "stdio"
        assert config.api_key is None or isinstance(config.api_key, str)
        assert "metricprovenance" in config.registry_url

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("ODGS_PROJECT_ROOT", "/tmp/test-project")
        monkeypatch.setenv("ODGS_API_KEY", "sk-odgs-test-key")
        monkeypatch.delenv("ODGS_REGISTRY_URL", raising=False)

        config = ServerConfig.from_env()
        assert config.project_root == "/tmp/test-project"
        assert config.api_key == "sk-odgs-test-key"

    def test_ensure_cache_dir_creates_directory(self, tmp_path):
        cache_dir = tmp_path / "test_cache" / "nested"
        config = ServerConfig(cache_dir=str(cache_dir))
        result = config.ensure_cache_dir()
        assert result.exists()
        assert result.is_dir()

    def test_default_cache_dir_in_home(self):
        config = ServerConfig()
        assert ".odgs" in config.cache_dir
        assert "cache" in config.cache_dir
