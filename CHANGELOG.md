# Changelog

## v0.3.1 — 2026-07-20

### Fixed (tier resolution)

- **Disk-cached tier is now bound to the API key that produced it.** Previously, any non-empty API key — a typo, an expired key, a revoked key — could inherit whichever tier was last successfully validated on that machine, for up to the 24h cache TTL, because the cache was only checked for freshness, not for which key wrote it. Only a completely absent key correctly resolved to `community`. The disk cache now stores a hash of the validating key and refuses to return a cached tier unless the current key matches it exactly. Legitimate repeat use of the same key is unaffected — the 24h fast path still applies. Added regression tests covering key mismatch, absent-key, and same-key cache-hit cases.
- **Community upsell notice no longer shown to Pro/Enterprise callers.** The informational notice appended to `validate_payload` and `governance_score` output ("your organization needs a certified licence...") was shown regardless of the caller's actual tier, including to callers with a validated paid licence. It's now suppressed once a Pro or Enterprise tier resolves.
- **`download_pack`'s success message now explains the two project-specific files** (`legislative/ontology_graph.json`, `executive/context_bindings.json`) a downloaded pack still needs before `validate_payload` will enforce it — these bind the pack's rules to your own process URNs and aren't part of the pack itself.

### Docs

- Removed forward-looking standardization-progress commentary from the README and PARTNERS.md; the standard and the software are two different things and this repo's docs should describe the latter.
- Protocol badge and prose brought current to the `odgs` 6.0.5 release.

## v0.3.0 — 2026-07-18

### Fixed (pack delivery)

- **`download_pack` now installs, not just caches.** Purchased bundles are materialized into an engine-bootable layout (`judiciary/standard_data_rules.json`, `sovereign/`, `manifest.json`) under the pack cache, and the tool returns the `project_root` to validate against. Previously the bundle was written as a single wrapped JSON file the validation engine could never read.

### Fixed

- **24h community-lockout bug** — A failed or unreachable API-key validation (network error or non-200 registry response) was persisted to the disk tier cache as `community`, locking licensed Pro/Enterprise users out of paid tools for the full 24h cache TTL. Failed validations are no longer written to disk; only successful (HTTP 200) validations are cached. Added regression tests covering network errors, HTTP errors, and recovery after an outage.
- **Installable `[bridges]` extra** — `pip install odgs-mcp-server[bridges]` was unresolvable: it pinned `odgs-databricks-bridge>=0.5.0`, but the latest published version is 0.4.x. All three bridge pins are now `>=0.4.0`.
- **Stale test** — `test_list_packs_includes_purchase_url` asserted a `brief_url` key that `list_packs` no longer returns (it returns `access_url`).

### Changed

- Upsell/licensing links now point to the self-serve pricing page (`metricprovenance.com/pricing`) instead of the partner brief (`/brief`), in the upgrade message, the community assessment notice, and the `list_packs` output.
- Development Status classifier raised from Alpha to Beta.

---

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
