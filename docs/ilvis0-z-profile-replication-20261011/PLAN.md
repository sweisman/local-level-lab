# Preselected recording calibration-transfer grid

Version `ilvis0-joint-z-profile-followup-v1`, study `replication`.
Selection is fixed by `docs/ilvis0-prediction-audit-20261011/replication-selection.csv`
and its receipt: only the earliest predeclared interval, `d9d91c8edba5721931856fc9`,
task `4876a722de50db44fd7a`, file `ILVIS0_applanix_57289_610_LVIS_38614965.013`.
Match the original 53-stretch selection, reference and source hash before freezing.
Never substitute another recording if it fails. The complete interval is 439 seconds
at median speed 793.61 km/h. Selection used no model fits.

Grid: Z gain {−2%, 0, +2%} × constant Z offset {−1, 0, +1 degree/hour}
× {specified-field globe, zero-field globe, stationary disc}: 27 identities.
Use only `bias1_unsubtracted`, fixed-zero removal. Original integration, header timing,
remaining bounds, original solver and initialization stages match the first grid.
Free normalized coordinates start at zero. Reestimate remaining parameters at every
node; this tests calibration robustness, not prediction with earlier calibration fixed.

One start/identity, at most 200 native sweeps/start and 5,400 total, no retries or
reserve. Count derivatives and both final predictions. The nominal-clock prediction
is fixed-parameter, not a clock refit. Execute after the removal grid with one worker
and two threads. Save all failures, derivatives, boundaries and residuals separately
from original results. Interpret shape first, field only after complete globe-favoring
comparisons. Grid nodes are not confidence limits; another date is not proof of
independent hardware. Preserve sealed hashes, measurements and environment; charge
before starting, retain interruptions as failures, and never restart after completion.
No second recording, additional case, prediction replication or corpus rerun is included.
