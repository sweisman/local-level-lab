# Matched fixed-time profile preparation

Begin with `50f24131843071ae9312c082`, unsubtracted processing and the zero-field
globe. This is the closest remaining comparison with six passing primary fits
but unresolved repeat agreement. Its two saved time offsets are approximately
−20.719 ms and −65.716 ms. Preserve their full recorded precision in the task freeze.

At each offset, fit all other active nuisance parameters twice: once from the
saved primary solution and once from the saved repeat solution. That gives four
conditional profile fits. Add the two previously completed smooth controls,
checked at their fixed time offsets. No latitude, model, recording or interval
selection changes are allowed.

## Proposed finite scope

- Four conditional nuisance fits, **80 native fitting calls each**, including
  the existing fresh final checks; no retries.
- One additional full-Jacobian diagnostic call per conditional fit.
- Two smooth controls, three fresh native calls each.
- **Six identities / 330 native calls maximum**, four total numerical threads.
  Recent timings imply roughly 1.5–2 hours at the ceiling.

The existing bounded trust solver and numerical tolerances remain unchanged.
The fixed-time adapter must expose every other active parameter and preserve
the original normalized physical bounds, observation weights and forward model.
Software controls must verify lifting/reduction, parameter order, full residual
agreement, both fixed-time anchors, boundary optima and failure propagation.

Freeze sources, inputs, original hashes, complete task identities, exact anchors,
environment, per-call accounting and controls before launch. Check all shared
locks and preserve interrupted starts. This document prepares the study; it does
not launch fits or charge an observed allowance.

## Interpretation

Compare completion and objective/track agreement between the two nuisance starts
at each identical time anchor. Report both anchors even if one fits worse. Include
the full timing derivative in each saved final diagnostic; holding time fixed
cannot establish stationarity in that direction.

Passing fixed-time fits remain diagnostic. A numerical shape conclusion still
requires the full free-time comparison, its scheduled repeat, all model/case
companions and the existing controls. This profile does not replace that gate or
authorize a wider rollout.
