# Changelog

## v0.2.0 — 2026-05-03

Modular scoring architecture and expanded test coverage.

### Changed

- **`governance_score`** — Refactored into a modular two-engine architecture:
  - **Fallback scorer** (default): Built-in 4-category heuristic evaluating Legislative, Judiciary, Executive, and Infrastructure planes. Identical scoring logic to v0.1.0 — no behavioural change for existing users.
  - **Maturity engine** (opt-in): When the `odgs-maturity` package is installed, the tool delegates to the authoritative 8-pillar DAMA DMBOK framework for deterministic governance assessment. This path is automatically selected at runtime; no configuration required.
- Added `engine` field to `governance_score` output indicating which scoring path was used. This is a **backwards-compatible addition** — no existing fields were changed or removed.

### Testing

- Expanded test suite from 9 to 20 tests.
- Separate test classes for the output contract, fallback scorer, maturity engine delegation, and import fallback behaviour.
- Added edge-case coverage: cryptographically signed rules, partial ontology graphs, empty projects.

### Compatibility

- **No breaking changes.** All v0.1.0 output fields (`score`, `grade`, `findings`, `breakdown`, `project_root`, `_odgs_notice`) remain unchanged.
- The `engine` field is the only new addition to the output schema.
- Minimum Python version unchanged at 3.10.

---

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
