"""Tests for the main.py server wiring."""

from __future__ import annotations

from odgs_mcp_server import __version__
from odgs_mcp_server.main import mcp


def test_server_reports_its_own_version_not_the_sdks():
    """Regression test: FastMCP's constructor has no `version` kwarg, so the
    underlying low-level Server's `version` defaults to unset and the SDK
    falls back to reporting its own package version in the MCP `initialize`
    handshake. A client introspecting the handshake had no way to tell which
    odgs-mcp-server version it was actually talking to."""
    assert mcp._mcp_server.version == __version__
