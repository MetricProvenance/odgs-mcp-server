# Changelog

## v0.1.0 — 2026-04-20

Initial public release of the ODGS MCP Server.

### Tools

- **`validate_payload`** — Enforce ODGS rules against live data payloads. Returns APPROVED/BLOCKED with violation detail and an `_odgs_notice` for compliance routing.
- **`governance_score`** — Assess project compliance maturity. Returns A–F grade, category breakdown, and actionable findings.
- **`list_packs`** — List available certified regulation packs (EU AI Act, DORA, GDPR, CSRD, NIS2, Basel III, and more).
- **`compile_regulation`** *(Pro)* — Compile regulation text into validated ODGS rule JSON.
- **`check_drift`** *(Pro)* — Detect semantic staleness in legislative definitions.
- **`detect_conflicts`** *(Pro)* — Cross-reference rules from multiple regulatory sources for contradictions.
- **`narrate_audit`** *(Pro)* — Convert cryptographic S-Certs into plain-language audit narratives.
- **`discover_bindings`** *(Pro)* — Auto-generate `physical_data_map.json` from a data catalog.
- **`sync_catalog`** *(Enterprise)* — Sync ODGS definitions with enterprise catalog platforms (Collibra, Databricks).

### Commercial Model

Partner-led IP licensing. See [PARTNERS.md](PARTNERS.md).  
Community tier is free and open (Apache-2.0).  
Pro/Enterprise certified packs are issued through Metric Provenance verified partners.
