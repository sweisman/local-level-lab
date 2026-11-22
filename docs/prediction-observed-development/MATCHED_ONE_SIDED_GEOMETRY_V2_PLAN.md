# Corrected matched geometry check

The first short preflight (`generated-matched-one-sided-v1-20261117-preflight`)
failed before native fitting because route was incorrectly passed as part of
the fixed four-field generated identity. It charged one start but made zero
native fitting calls. Preserve that terminal record; do not rerun it.

This separately versioned study uses the same finite scientific question and
limits described in [the original plan](MATCHED_ONE_SIDED_GEOMETRY_PLAN.md).
Route is now a property of the generation recipe. All three candidate fits
still receive one shared generated measurement set per route. A focused test
requires the four-field identity to remain unchanged while straight versus
turning changes only the route in that recipe.

Qualify the corrected source and task-level recovery, then run a new short
three-candidate preflight. If it passes, freeze and run the two-route,
six-fit study. Preserve all failures, costs, original stopping verdicts,
withheld predictions and physical-adequacy results. The rule remains a
research-only numerical candidate; no observed or reserved ESA data is used.
