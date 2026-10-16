# Continue only the unstarted timing checks

The stopped timing-boundary diagnostic has nine charged identities: eight saved
results and one interrupted identity. Its incomplete journal is preserved unchanged.
The [read-only accounting audit](../ilvis0-accounting-audit-20261016/README.md)
verifies those outcomes and identifies twelve identities that never started.

## Fixed scope

- Exactly the twelve unstarted identities, retaining their original identifiers,
  observations, endpoint values and task order. No retry of any charged identity.
- Twelve time-only starts maximum; zero joint nuisance-fit starts.
- Twenty-six native evaluations per identity, **312 maximum**, no retries.
- Reserve the full 234-call allowance of the nine earlier starts. Combined identity
  allowances remain **546**, with no increase to the original study's ceiling.
- One numerical worker, four threads, zero reserved threads; roughly two to three
  hours at the observed native-call runtime if the allowance is exhausted.
- Reuse both verified passing controls and all eight saved checks, retaining the
  interrupted identity as unresolved. No completed checks are rerun.

The numerical model, calibration bounds, receiver covariance, integration clock,
native kernel, timing-search method and two-sided stopping tolerances remain
unchanged. The source/environment/input freeze includes the old manifest, journals,
failure record, saved results and native artifacts. The parent worker lock remains
held throughout continuation to prevent simultaneous execution of the old worker.

## Accounting qualification

The [receipt-ledger qualification](../ilvis0-receipt-qualification-20261016/RESULTS.md)
passed eighteen controls. Each charge is now an individual hash-chained receipt
with an atomically updated head. Both must be flushed before native execution.
Short writes are completed explicitly; incomplete transactions block further work
without repair. The old append ledger and its stopped worker remain untouched.

Preserve the initiating exception before any later accounting read. The immutable
receipts are authoritative; line-based exports are derived publication artifacts.
Metadata-only packaging performs no native calls and cannot restart completed work.

## Interpretation

This is continuation of the declared diagnostic population, not selection for good
fit results. It does not authorize changing the physical assumptions or adding
fitting attempts for completed, failed or interrupted identities. A passing local
check alone cannot relabel a stretch; all required model/case companions, controls
and repeat agreements remain necessary. Scientific decisions still abstain.
