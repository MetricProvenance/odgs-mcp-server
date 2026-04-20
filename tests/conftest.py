"""Shared test fixtures for the ODGS MCP Server test suite."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def odgs_project_root(tmp_path: Path) -> Path:
    """Create a minimal ODGS project structure for testing."""
    # Legislative plane
    legislative = tmp_path / "legislative"
    legislative.mkdir()
    (legislative / "ontology_graph.json").write_text(json.dumps({
        "nodes": [
            {"urn": "urn:odgs:concept:transaction_value", "label": "Transaction Value"},
            {"urn": "urn:odgs:concept:aml_flag", "label": "AML Flag"},
            {"urn": "urn:odgs:concept:kyc_status", "label": "KYC Status"},
        ],
        "graph_edges": [
            {
                "source_urn": "urn:odgs:rule:R001",
                "target_urn": "urn:odgs:process:aml_check",
                "relationship": "BLOCKS_PROCESS",
            },
        ],
    }))
    (legislative / "standard_metrics.json").write_text(json.dumps({
        "metrics": [
            {"metric_id": "M001", "name": "Transaction Completeness", "urn": "urn:odgs:metric:M001"},
        ],
    }))

    # Judiciary plane
    judiciary = tmp_path / "judiciary"
    judiciary.mkdir()
    (judiciary / "standard_data_rules.json").write_text(json.dumps({
        "rules": [
            {
                "rule_id": "R001",
                "urn": "urn:odgs:rule:R001",
                "name": "AML Threshold Check",
                "logic_expression": "value <= 100000 or aml_flag == True",
                "severity": "HARD_STOP",
                "version": "1.0.0",
            },
            {
                "rule_id": "R002",
                "urn": "urn:odgs:rule:R002",
                "name": "KYC Verification",
                "logic_expression": "kyc_status == 'VERIFIED'",
                "severity": "SOFT_STOP",
                "version": "1.0.0",
            },
        ],
    }))

    # Executive plane
    executive = tmp_path / "executive"
    executive.mkdir()
    (executive / "context_bindings.json").write_text(json.dumps({
        "contexts": [
            {
                "context_id": "urn:odgs:process:aml_check",
                "rules": ["urn:odgs:rule:R001", "urn:odgs:rule:R002"],
            },
        ],
    }))
    (executive / "physical_data_map.json").write_text(json.dumps({
        "mappings": [],
    }))
    (executive / "business_process_maps.json").write_text(json.dumps({
        "processes": [],
    }))

    # Schemas
    schemas = tmp_path / "schemas"
    schemas.mkdir()

    # System (for hashing)
    system = tmp_path / "system"
    system.mkdir()
    scripts = system / "scripts"
    scripts.mkdir()

    return tmp_path


@pytest.fixture
def passing_payload() -> dict:
    """Data payload that should PASS AML validation."""
    return {
        "process_urn": "urn:odgs:process:aml_check",
        "data_context": {
            "value": 50000,
            "aml_flag": False,
            "kyc_status": "VERIFIED",
        },
    }


@pytest.fixture
def failing_payload() -> dict:
    """Data payload that should FAIL AML validation."""
    return {
        "process_urn": "urn:odgs:process:aml_check",
        "data_context": {
            "value": 200000,
            "aml_flag": False,
            "kyc_status": "VERIFIED",
        },
    }
