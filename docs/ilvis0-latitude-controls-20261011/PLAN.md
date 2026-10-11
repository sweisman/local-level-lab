# Qualification away from the equator

Goal: test whether the completed 200 Hz correction improves calibration recovery
away from the equator, and demonstrate why increment conventions cannot be mixed.
This implements the [next-step proposal](../ilvis0-compensation-controls-20261011/NEXT_STEP.md).
No NASA input, observed optimizer starts, production promotion or git operations.

## Frozen matrix and budget

Use 12-second, 220 m/s constant-latitude tracks at 1,000 m, at +45° and −45°.
Generate all three physical truths independently from analytic motion and eight-point
Gaussian quadrature. Ordinary body-rate integrals are supplied to the unchanged
combined-correction candidate. Keep the six original calibration limits, 24 off-grid
receiver observations, original solver and 200-sweep allowance including two final
prediction sweeps. No attempts are repeated.

Two constructions: nominal 200 Hz with interior calibration and pitch/yaw; variable
spacing (the original ±50 ppm control) with near-boundary calibration and added
±0.35 radian roll. Both constructions run from zero and the original opposed start.
The crossed identity matrix is 3 truths × 2 latitudes × 2 constructions × 2 starts:
**24 starts maximum**, at most **4,800 sweeps** for fits. These are software controls,
not flight simulations or independent scientific trials. Expected runtime is a few
minutes; the sweep allowance, rather than elapsed time, is binding.

Before fitting, make 24 known-calibration predictions: original and combined
integration for each of the 12 constructions. Six additional already-compensated
controls use endpoint receiver observations, one per truth/latitude. For each, make
two predictions: the explicitly supported original treatment and a deliberately
mislabelled-input diagnostic demonstrating double correction. The convention guard
must reject enabled compensation when input is correctly labelled already compensated.
These 12 predictions add no optimizer starts. Total ceiling: **4,836 native sweeps**.

Pass criteria for each fit: independently generated track prediction below 2 mm,
known-calibration prediction below 2 mm, numerical convergence, and objective no
higher than the known-calibration objective plus 0.01. Report calibration errors,
active limits and conditioning separately; these pass criteria do not imply unique
calibration. Preserve failures and charged interrupted starts without retries.

## Implementation and verification

- Add `analysis/lll/ilvis0_latitude_controls.py`: independent latitude-aware Euler
  motion, local Earth/transport vectors, receiver metrics and quadrature. Construct
  a precisely defined finite-increment convention from analytic attitude endpoints
  and independently integrated force, rather than calling a production predictor.
- Add `analysis/tests/test_ilvis0_latitude_controls.py`: both hemispheres, all models,
  axes/signs via finite differences, force/frame identity, known-calibration native
  predictions, independent ODE validation of finite increments, explicit convention
  guard, unequal spacing and invalid inputs. Watch new tests fail before implementation.
- Add `build_report.py` here: verify prior frozen sources, seal source/environment/
  build hashes before numerical starts, exclusive lock, fsynced append-only starts,
  atomic results and completion, no retries, saved-only publication mode.
- Publish CSV comparisons, findings, exact budget and a separate hash receipt.
  Packaging must preserve numerical files and journals. Update current roadmap links.

The already-compensated convention here is an explicitly constructed mathematical
control, not an assertion about Applanix firmware. Endpoint observations isolate
full-packet treatment; arbitrary partial finite increments require a separately
defined convention. Do not silently reinterpret those inputs or invent archival samples.
Full nuisance freedom, long records, noise and independence remain later qualifications.
