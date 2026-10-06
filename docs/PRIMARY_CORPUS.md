# Provisional primary corpus (policy pilot-2, software 0.6.0)

All structurally valid uploads remain public, unmodified CC0 archives. Publication does not confer scientific eligibility. Only a curator's local CLI can approve provenance; uploaded install IDs, unit IDs, synthetic flags and purported certificates cannot establish it.

## Operator workflow

Use `lll-server --data /path/to/data` before each command:

1. `register-unit "private operator reference"` creates an opaque physical-instrument ID. The curator must verify the physical instrument and avoid registering it twice.
2. Complete **every** check in BENCH.md, retain the evidence, and prepare a JSON certificate:

```json
{
  "tier": "usable",
  "checks": {
    "decode": true, "sample_rate": true, "scale": true,
    "autozero": true, "range": true, "stability": true,
    "reversal": true, "recovery": true, "temperature": true
  },
  "config": {"rate_hz": 100, "gyro_range_dps": 2000, "accel_range_g": 16, "auto_zero": false},
  "source_sha256": ["replace with the 64-character SHA-256 of each bench evidence archive"]
}
```

3. **Before the flight**, run `certify-unit UNIT evidence.json`. It stamps approval time now; a supplied timestamp cannot backdate approval. Changing settings requires a new certificate. The checks are explicit curator attestations, not automatically inferred from a flight calibration.
4. Upload and `process` the flight. Verify its physical provenance, then run `approve-session SESSION CERTIFICATE`. The export includes public provenance.json for auditing eligibility; it omits operator identities. Approval binds the exact archive hash to the registered instrument and its certificate. A later bench approval cannot qualify an earlier flight.
5. Run `collate`. `revoke-session SESSION` withdraws approval; rerun `collate` to regenerate the published report.

There is no public administrative endpoint. Protect the data directory and CLI credentials. This is a controlled research corpus, not cryptographic proof of a physical flight: trusted curators must inspect evidence and prevent duplicate physical registrations.

New app sessions require operating-carrier selection, a consistent flight number, departure-local
date and route codes. This is collection metadata, not curator approval: `track_verification` stays
`pending`, and neither directory membership nor opening the history page proves that a flight flew.
A dated actual track can support a provenance review and GPS cross-check. Keep it separately with
its provider terms and source; it does not replace the archive hash bound by approval. Missing-GPS
IMU recordings remain publishable/exploratory. External-track substitution has no implemented or
validated primary policy and cannot bypass the current scientific gates. See
[PROTOCOL.md](PROTOCOL.md) and [VALIDATION.md](VALIDATION.md#external-flight-tracks-and-missing-gnss).

## Eligibility

Primary flights also require both calibrations, 60 retained cruise minutes, identified curvature, acceptable prior and WMM selection sensitivity, and two retained course groups separated by at least 30°, each containing at least 600 seconds. These heading thresholds are provisional. Single-heading flights remain exploratory even when IMU reversals improve identifiability.

Heading groups are permutation-invariant: normalize bearings, sort them, cut after the largest
empty circular gap (ties choose the smallest following bearing), then apply the existing
strictly-less-than-10° grouping rule in that canonical order. Missing turn samples beyond three
expected periods leave orientation unresolved and exclude all subsequent epochs. Inference
nonconvergence and conflicting same-time GNSS fixes also exclude primary use.

`analysis/lll/policy.py` centralizes integrity exclusions: inconsistent ranges, significant corrupt bytes, mixed instruments, unverified configuration, unresolved orientation and recording data loss. A current exploratory instrument observation can downgrade a certificate. An unverified upload cannot downgrade a certified instrument through a fabricated matching unit ID.

Ground population pooling is disabled. Reports label confidence intervals and significance nominal and remain provisional until real WT901 bench validation and an adequately powered null-tail calibration are complete. `--include-synthetic` is explicitly a simulation mode; it is never used by server collation.

## Migration and deployment

Schemas 2 and 3 remain readable; historical raw archives are never rewritten. Missing historical provenance, configuration evidence or fresh per-calibration latitude stays unknown. Reprocess existing sessions explicitly with `process SESSION...`, then collate again; old generated reports are not automatically upgraded. Server collation uses only successfully processed results from the current software version.

To migrate all stored sessions, run `process --reprocess`, check failures, then `collate`.
The standalone collation gate also excludes results whose analysis version is not 0.6.0 or whose
convergence diagnostic is absent. Raw archives and their approval hashes remain unchanged.

The server admits at most two concurrent uploads across workers sharing its SQLite database. Bodies are bounded before multipart parsing (archive limit plus 64 KiB framing allowance), spool to disk, and are hashed and validated in a worker thread. There are separate persistent hourly attempt and accepted-session quotas. Duplicate archives do not consume accepted quota. Admission leases expire after six minutes; requests time out after five. Deploy behind a reverse proxy with body, connection and rate limits, adequate temporary-disk capacity, and a single shared local data directory. Separate servers with separate SQLite databases do not share quotas.

Android journals preserve complete local records across process death. Recovery truncates incomplete tails and conservatively excludes the session from primary results. Upload jobs use immutable snapshots and the destination selected at consent time. Legacy gzip recordings can still be shared; start a new session to record with journals.

Recovery retains the foreground service and Bluetooth connection while configuration verification
is pending; explicit stop invalidates queued retries. Upload work is keyed by session, destination,
and archive digest. Retries retain snapshot bytes; terminal work (including cancellation) removes
the snapshot. Acknowledged archive and manifest digests persist independently of it.
