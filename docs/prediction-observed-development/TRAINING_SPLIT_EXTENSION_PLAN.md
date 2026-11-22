# Extend the same ESA fit to a longer horizon

The 600/200 recheck covers all 200 nominal height ranges, while a different
fit to reports 0–799 fails on reports 800–1199. This development-only test
separates forecast length from the changed fit: hold the **already sealed
600-report calibration** fixed, extend its raw forecast to report 999, and
condition that longer forecast on only reports 0–599. Compare reports 800–999
with the earlier 800-report-fit forecast on the same 200 receiver positions
only after the extension closes. Neither result is independent validation.

Use development recording 187, the same selected interval, globe-with-specified-
field candidate, header-elapsed clock, linear-point rate convention, receiver
policy, nuisance bounds and both declared IMU input-error laws. Stage only
reports 0–599 as observations. Stage original IMU increments through report
999 and query times through 999; keep reports 600–999 out of every worker.
Source-bound preflight found 299,867 complete increments for this extension.
The seven reserved ESA groups remain unopened.

For each law, reconstruct the **same training problem** from the frozen early
input and fit point, without an optimizer call. A native forecast must reproduce
the old 600/200 raw forecast on its first 800 query times within 1 micrometre
in each local position vector before any extended result is accepted. Rebuild
the declared error operator through report 999, replay the original training
cost and covariance log determinant, and condition on the first 600 residuals
only. Save the raw and conditioned extended paths and nominal covariance
before opening any scored receiver positions. A failed prefix or replay gate
abstains; it is not repaired by selecting another law.

Before observed work, pass generated fixed-point extension and no-leak tests,
source-bound qualification and a finite reboot-recovery control. Freeze source,
input and numerical-environment hashes. Allow exactly two original tasks, one
per predeclared law, with one start each, **no optimizer evaluations**, at most
500,000 native calls and 2 billion packet/query visits per task, two workers
of one thread, and a 10,800-second cooperative wall cap. Preserve all charges
and numerical failures. An unchanged technical interruption may resume only
under separately frozen finite limits; no completed task may be rerun.

The saved-only score will report north/east/up errors, coverage and fit/bound
provenance for reports 600–999, with the overlapping 800–999 period compared
against the earlier sealed 800/400 result. No error law may be selected by
those later errors. Absolute adequacy, calibrated coverage and any Earth-model
decision remain open.
