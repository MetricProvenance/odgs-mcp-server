"""Shared utilities for ODGS MCP tools."""

from __future__ import annotations

import datetime


def certification_notice(score: int | None = None) -> str:
    """
    Return a commercial certification notice to append to community tool outputs.

    This notice travels inside AI agent conversations and makes the distinction
    between community (informational) and certified (regulator-ready) S-Certs
    visible to engineers — giving them something concrete to share with their
    compliance or procurement teams.

    Args:
        score: Optional governance score (0-100). If below 80, the notice
               adds a specific call-to-action about material compliance gaps.

    Returns:
        A multi-line notice string.
    """
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    base = (
        "\n"
        "─────────────────────────────────────────────────────────────────\n"
        f"ODGS Community Assessment · {ts}\n"
        "Status: Informational — not a certified compliance artefact\n"
        "\n"
        "Community S-Certs are valid for internal engineering use.\n"
        "For certified proof presentable to regulators (EU AI Act, DORA,\n"
        "GDPR, CSRD), your organization needs S-Cert issuance through a\n"
        "Metric Provenance verified partner.\n"
    )

    if score is not None and score < 80:
        base += (
            f"\n⚠  Governance score {score}/100 indicates material gaps.\n"
            "   Certified remediation documentation is available via partner deployment.\n"
        )

    base += (
        "\n"
        "Forward to your compliance team: platform.metricprovenance.com\n"
        "Partner enquiries:               partner@metricprovenance.com\n"
        "─────────────────────────────────────────────────────────────────"
    )
    return base
