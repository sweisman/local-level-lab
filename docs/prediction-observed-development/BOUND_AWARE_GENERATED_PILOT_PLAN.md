# Bound-aware complete-fit generated pilot

## Fixed question

Can the existing affine bound-aware forecast calculation run through the
complete noisy 26-parameter fit, preserving the raw forecast, all calibration
columns, the known physical truth and every failure label?

This is a **technical pilot**, not a coverage or aircraft adequacy test. Its
task pass means that the saved bounded artifact and original score are
complete and consistent; it does not turn a failed physical path into a pass.

## Finite design

- Generate two new, independent cases: increment-law seed **610101** and
  point-law seed **610102**. Each uses the existing 300 Hz, 900-second
  generated aircraft route, 900 one-second receiver reports, first 600 for
  training, last 300 withheld, one start, 26 fitted nuisance directions and
  the specified-field globe. Retain the existing bounds, receiver weighting,
  clock and original 10 m physical accuracy screen.
- Wrap the existing earlier-only forecast diagnostic with
  `bounded_forecast_wrapper.evaluate`. Allocate 0.025 error probability to
  calibration and 0.025 to future noise; retain all 300 later positions in
  the affine envelope. Save the bound artifact and the unmodified raw and
  conditional forecasts before generating later truth.
- First qualify a ten-second, nine-query frozen-worker preflight, source
  tests and reboot recovery. Then run exactly two full tasks, at most 200
  evaluations each, two workers of one numerical thread, six-hour
  cooperative wall limit. Charge and journal all native work before use.
- Count technical artifact failures, numerical stopping failures, physical
  accuracy failures and interval misses separately. Do not use a favorable
  prefix or change the screen after seeing results.

No original NASA or ESA recording, scored aircraft result or reserved flight
group may be read. A passing affine software pilot cannot establish nonlinear
or observed-aircraft coverage; those need an independently frozen cohort and
an explicit nonlinear remainder allowance. The scientific decision is
**abstain**.
