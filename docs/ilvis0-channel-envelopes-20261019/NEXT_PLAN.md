# Whole-history contribution comparison: preparation requirements

The snapshot study is complete. This continuation needs its own source/input/
environment freeze and finite allowance; its predecessor cannot restart.

1. Reuse the two sealed extractions after verifying their cache hashes against
   the completed extraction artifacts. Do not rescan originals or select new
   recordings based on snapshot outcomes.
2. Form fixed consecutive 200-packet groups on the saved preselected stretch.
   Keep the same integer observations under both clock hypotheses. Use receiver
   support margins to exclude unsupported edge groups before model residuals;
   publish the exact covered duration, discarded edges and completeness rules.
3. Qualify continuous averaging about a central receiver estimate against
   independent known histories. A central estimate is not an instantaneous
   replacement for a packet group's force. Preserve common latency and actual
   integration periods; do not interpolate packet measurements.
4. Carry the same declared receiver, smoothness, gravity, count and calibration
   assumptions into all candidates. Keep deterministic error separate from an
   uncalibrated likelihood. Changing a physical assumption requires a new,
   explicitly named sensitivity case rather than editing snapshot evidence.
5. Test a single shared calibration across the history. A fixed feasible point
   may certify only the relaxed scalar constraints it actually satisfies; it
   cannot establish jointly feasible receiver perturbations, orientation or a
   full gyro-free trajectory. If an optimizer is needed, qualify the changed
   objective independently and freeze its start/evaluation limits first.
6. Compare with the saved complete-observation result on the same recordings,
   state support differences, preserve all unsupported groups and failures,
   and withhold a new scientific decision. No archive-wide fitting follows.

The shared-error/prediction work remains ready to progress independently of
this necessary-constraint diagnostic. It must use training observations only
and preserve uncertainty from nuisance and covariance estimation.
