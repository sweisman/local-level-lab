# Long-history screen of source derivative bounds

Launch only after the separately frozen source-derivative native qualification
passes all 24 controls. Preserve its candidate and unchanged physical bounds.

Use the same six generated 1,600-packet sources, saved training constraints,
calibration boxes and future query times as the completed source screens.
Compute one new bound per source. Compare identical reference maps first,
then retain the minimum of the original, compiled, batched-source and new
allowances on each axis. Do not round-trip those bounds through displayed
metre values when forming the minimum.

## Separate finite allowance

- Six identities, one bound each, at most 76,800 logical bound steps.
- Six setups and 36 exact training-support checks.
- Reserve 9,600 source-reference steps and 9,600 trained body bounds.
- Separately reserve six derivative setups and 9,600 compiled derivative
  appends covering reference/domain midpoint/end states.
- Four single-thread workers; cooperative 120 seconds per bound and 600
  seconds overall. No retries, native trajectory evaluations or optimizer starts.
- No aircraft originals, LP proposals or protected ESA observations.

Freeze sources, inputs, comparison artifacts, compiler and environment before
launch. Preserve failures and charges. Passing establishes source-map
compatibility and completion on these histories. A separately frozen complete
prediction comparison must still meet every original horizontal and vertical
width target before withheld aircraft fitting proceeds. These are software
development calculations, not new observational evidence or calibrated coverage.

[Native qualification](../ilvis0-taylor-native-controls/README.md) ·
[Previous long-history screen](../ilvis0-batched-range-preflight/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
