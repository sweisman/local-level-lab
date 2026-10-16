# Next diagnostic: native two-sided timing checks

The software gate passed 43/43 controls. The saved-clock screen supports reliable
side geometry for all eleven unfinished primaries and all eight unfinished repeats.
Two unsupported endpoint geometries belong to already-passing smooth repeats;
three passing smooth repeats overall remain in different timing basins. Their
existing results must be retained rather than moved to a convenient knot.

The next work targets all six remaining stretches. It is a timing-location and
stopping diagnostic, with every nuisance parameter held at its saved value during
timing location, followed by the qualified full-nuisance stopping probes.

## Prepare and qualify the adapter

Use the actual double-precision clock comparison, retaining separate receiver
transitions. A nearest transition changes only one receiver epoch in this screen;
it need not be the transition where the total timing gradient changes sign.

Enumerate the representable transitions within ±1 microsecond of each unfinished
endpoint. Test the timing gradient outside this cluster and, when it brackets a
negative-to-positive change, use a bounded search over the discrete transitions.
Verify the chosen knot and both adjacent intervals with the clock oracle.
This search estimates a time coordinate and must be recorded as an observed
time-only optimization start, even though no joint nuisance fit is performed.

Software controls must cover multiple clustered transitions, nonmonotone interior
gradients, absent brackets, derivative discontinuities, floating-point plateaus,
finite search limits and failed nuisance stability. Retain all physical bounds
and numerical tolerances. A failed bracket or an unchecked neighbor must abstain.

## Proposed finite observed scope

- Nineteen time-only starts: all eleven unfinished primaries and their eight
  unfinished repeats. Reuse the three hashed passing repeats unchanged.
- Two existing smooth completed controls, checked without boundary relocation.
- **Twenty-one identities / at most 26 native evaluations each / 546 total**,
  four total numerical threads, no retries. No joint nuisance-fit starts.
- Limit timing location to at most twelve native gradient samples, followed by
  the ten-call two-sided check. Reserve the remaining calls for the original
  point and reproduction/relocation checks; never enlarge a started allowance.
- Expected ceiling is roughly two to three hours at measured native speeds.

Freeze source/input/environment hashes and originals, task identities, control
and repeat rules, scalar-clock query limits and the native-call journal before
launch. The runner must qualify before this prospective scope becomes executable;
this preparation does not launch or charge observed work.

Report old versus new timing, objective, physical prediction changes, both side
checks and all scheduled repeat agreements. A time relocation must reproduce
the original prediction and cost within the preserved stability tolerances.
The bounds, models, receiver weights, nominal clock and processing hypotheses
are unchanged. Scientific decisions still abstain. A later combined numerical
preference requires every model/case, control and repeat check; partial native
success does not change a stretch's disposition.

The smooth repeats in different basins may subsequently require a small profile
with nuisance reoptimization. That is a separate finite study, after the timing
checks establish which endpoint cases remain problematic.
