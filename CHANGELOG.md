# Changelog

All notable changes to the maintained `alessbarb/ha-ideenergy` fork are documented here.

## [3.0.0a3] - 2026-09-07

First maintained-fork prerelease built from the upstream 3.x alpha line.

### Reliability and authentication

- Removed the unconditional session keepalive that previously ran on every coordinator tick.
- The coordinator now stays passive when no dataset is due and preserves the existing 6-hour/12-hour success throttles and 5-minute failed-attempt throttles.
- Client failures propagate through Home Assistant as update failures instead of being hidden as successful refreshes.
- Authentication recovery has a single owner: the pinned `ideenergy` client performs session refresh, one bounded 401/403 retry and circuit-breaker handling; the Home Assistant coordinator does not add a second retry loop.
- Repeated API failures are bounded by the maintained client circuit breaker instead of producing unbounded automated traffic.

### Data correctness

- Historical zero-energy periods are preserved instead of being discarded as falsey values.
- Historical states are sorted before hourly aggregation, so statistics no longer depend on API response ordering.
- Existing statistic sums reuse the snapshot supplied by `homeassistant-historical-sensor` instead of performing a redundant recorder lookup.
- The maintained client preserves decimal accumulated-meter readings rather than truncating them to integer kWh.
- Historical periods in `Europe/Madrid` correctly handle 23-hour and 25-hour daylight-saving transition days.
- Reversed historical date ranges are normalized without collapsing the requested interval.
- Invalid power-demand limit responses now raise the client's explicit error contract instead of an `AssertionError`.

### Home Assistant lifecycle

- Config entries use the CUPS as a stable unique identity and prevent duplicate configuration of the same supply point.
- Existing entries without a unique ID can be migrated to the CUPS identity.
- Invalid credentials raise the Home Assistant authentication lifecycle and temporary service errors use retryable setup behavior.
- Reauthentication and reconfiguration preserve the existing supply-point identity.
- Removed the deprecated double-reload pattern involving config-entry update listeners.
- Added privacy-safe diagnostics for coordinator health and active/cached dataset types.

### Privacy

- Normal logs and exception strings no longer expose usernames, passwords, contract IDs, CUPS-based entity IDs, request URLs containing identifiers, raw API payloads or household energy values.
- Diagnostics redact credentials and CUPS and deliberately omit raw consumption/generation histories and direct meter readings.

### Compatibility and validation

- Added pull-request CI and functional Home Assistant tests.
- The supported minimum is now Home Assistant 2026.3.1 and is tested explicitly.
- The same functional suite is also tested against Home Assistant 2026.9.1 on Python 3.14.
- HACS, Hassfest and CodeQL remain part of the validation gates.
- The integration pins the maintained `alessbarb/ideenergy` client to immutable commit `c16442d36a5b59f6d3f895ebdd722654bf54fcf1`.

### Documentation and maintenance

- README/FAQ now describe the actual 3.x behavior rather than the obsolete 2.x instant-sensor and minute-50-to-59 retry model.
- English and Spanish installation/support links point to the maintained fork while preserving original authorship and GPL-3.0 licensing.
- The 2.x → 3.x upgrade guide no longer instructs users to edit Home Assistant `.storage`, run ad-hoc Recorder SQL or modify coordinator constants to force backfill.
- Migration guidance now starts with a full backup and preserves existing Recorder statistics by default.

### Known limitation

- Native SMS/OTP two-factor authentication is not implemented. The private i-DE web API does not currently expose a documented, stable OTP challenge contract that can be implemented safely. If i-DE requires an SMS verification challenge, complete it through the official i-DE website or app.
