# Check adjacent timing boundaries

The completed boundary review leaves five stretches unresolved. This follow-up
preserves every original measurement, physical bound, receiver weight, integration
clock and earlier numerical outcome.

## Saved-result diagnosis

- `0e73879f98c3b701fd7c42df`: one primary has timing cells too narrow for the
  qualified probes. Its other primary/repeat pair passes individually but differs
  by 2.24 cm on one axis and 6.42 × 10^-6 in relative cost, exceeding repeat limits.
- `370cec66878c4c1cf84b4ceb`: one right-side probe is nonstationary; the required
  repeat was interrupted. Neither failure is recoverable by republishing metadata.
- `50f24131843071ae9312c082`: the repeat has no transition within the declared
  search window. The adapter correctly performed zero evaluations, but the old
  worker then looked for a nonexistent cached evaluation. Its older primary and
  repeat costs already differ beyond the repeat threshold; a reporting repair
  alone cannot resolve the stretch.
- `b4e44ddc0f130ecd45674c78`: two probes reach an unchecked neighbor while also
  making large nuisance corrections. Gravity moves across its entire allowed
  range, and vertical prediction changes exceed 3 m. These cannot pass as small
  timing corrections. Other endpoints have unsupported side geometry.
- `bb8061a43b4f14b6262ceda1`: both unfinished checks meet the numerical movement
  and stationarity limits but reach an unchecked adjacent timing boundary. The
  largest saved per-axis epoch displacement is below 0.24 mm. This is the narrow
  first target for an additional boundary check.

These observations come from the sealed review and continuation metadata. They
are not new integrations or changed convergence labels.

## Candidate and software controls

Keep the original ten-call, full-nuisance, two-sided check unchanged. A separate
wrapper may follow exactly one unchecked neighbor only when every other branch
passes and the rejected branch passes all existing stationarity, cost, continuity
and physical-movement limits. Recheck the reached point on both sides, with all
nuisance parameters active. Require its clock geometry to be independently
supported. Never treat an unchecked edge as a pass.

Allow at most three complete checks per identity: **30 native calls**, no retries.
Compare every relocated center with the initial center under the original cost
and 1 mm RMS / 1 cm maximum movement limits. Multiple unresolved branches, large
corrections, unsupported geometry, cycling or exhaustion must abstain. No tolerance
changes, arbitrary knot merging or frozen nuisance directions are permitted.

Software controls must include a known neighboring cusp minimum, a monotone
nonminimum, large nuisance movement, unsupported geometry, multiple unresolved
branches, finite-call exhaustion and unchanged tolerances. Also reproduce the
zero-evaluation reporting case without archive data. Preserve the old workers.

## Finite observed scope after qualification

Exactly four identities: the predeclared `bb8061a43b4f14b6262ceda1` unsubtracted
zero-field-globe primary and repeat, plus the two existing smooth controls.
The target endpoints may each use 30 native calls; each unchanged smooth control
may use three: **66 calls maximum**, four total numerical threads, no retries.
Record two local joint-nuisance continuation starts and two control identities.
This is a separate freeze and does not reuse an older study's remaining allowance.

Freeze sources, original/input hashes, endpoint values, environment, identities
and limits before launch. Use immutable per-call receipts and exclusive locks.
Both controls must pass before the targets run. A later numerical preference
requires the primary, repeat, their existing agreement test and all companion
models/cases. The other four stretches remain outside this observed scope.
