# Fixed-point horizontal correction checks

Use all twelve endpoints from the completed horizontal full-calibration
qualification. Freeze the parent and saved correction-audit hashes. At each
endpoint evaluate exactly three points: the saved center, its original local
bounded correction and its diagnostic column-scaled ridge correction.

The two correction vectors come from the completed saved-array audit; do not
re-solve them or select a vector after seeing native results. Retain all
26/27 nuisance columns and the same independent generated observations,
nominal clock, physical bounds and projected covariance.

Require the center to reproduce saved residuals and tangents. Report fresh
stationarity, actual versus linear cost, retained-coordinate motion, unscored
height errors and whether the unchanged 1e-4 stationarity /1e-8 relative-cost
/1 mm axis-RMS /1 cm epoch-maximum numerical limits pass. These fixed-point
checks cannot relabel fits, qualify a solver or satisfy paired-start fitting.

## Frozen allowance

- Twelve endpoint identities, three points each: **36 native tangent calls**.
- Zero nonlinear optimizer starts, original-recording reads or retries.
- Four total numerical threads; **120 seconds after kernel compilation**.
- Freeze exact sources, environment and input hashes before launch. Use an
  exclusive lock, pre-call durable journal and atomic hashed result artifacts.
- Completed or charged work cannot restart; saved-only publication makes no calls.

Passing ridge probes would justify a separately tested candidate. They do not
authorize observed refits, change the failed qualification or address its
remaining zero-field globe cost-repeatability failure by themselves.
