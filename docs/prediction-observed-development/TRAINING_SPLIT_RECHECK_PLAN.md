# Earlier-only check of the ESA error law

The current 800/400 development forecast has small horizontal error but its
conditional height correction moves the wrong way later. This new **retrospective
development diagnostic** asks whether that failure was already visible using
only an earlier part of the same recording. It does not provide independent
validation: all 1,200 receiver reports have previously been opened.

Use the existing selected 20-minute interval from ESA development recording
187. Fit only receiver reports 0–599 and the corresponding IMU prefix. Hold
reports 600–799 out of fitting, initialization, starts, error-law selection and
conditional updates. The existing 800–1199 scored section is not an input to
this task. Keep the recorded motion, `sphere_rotating` model, header-elapsed
clock, linear-point rate interpretation, original bounds, receiver policy and
the two already declared IMU input-error laws. Use the same prespecified
starts and numerical stopping checks; failed fits abstain.

For each qualified law, save the uncorrected and earlier-conditioned forecast
through report 799, full north/east/up errors, nominal intervals, rank and
bound status. Compare the 600/200 result with the already sealed 800/400
result only **after** the new task closes. Do not choose a law by its held-out
error, change a limit, or recast this as a model decision. The question is
whether the current law gives useful warning on an earlier, shorter horizon.

Before any observed fit, qualify a 600/200 training-only split and recovery on
known-answer controls. Freeze source/input/environment hashes, one task per
law, at most four total threads and finite starts, evaluations, native work
and wall time. Preserve numerical failures. The seven reserved ESA groups
remain unopened. A new scientific decision requires separate adequacy and
coverage qualification.

The preparation check now passes on the sealed development source: it stages
600 earlier receiver reports, 200 reports for separate later scoring, and
239,867 IMU increments ending at the old 800-report boundary. The training
payload excludes the scored receiver values. A generated 600/200 control shows
that changing all scored heights leaves every staged training input unchanged;
the existing task-recovery checks also pass (11 focused tests together).
The fit and its source-bound study qualification have not yet run.

The prepared two-task adapter keeps the original `sphere_rotating` candidate,
start zero, 200-evaluation cap, original 26 calibration columns, and both
declared input-error laws. Its separate allowance is at most 700,000 native
calls and 45 billion packet visits per law, with a 14,400-second study wall
limit. Two workers reserve one numerical thread each. It does not stage the
200 scored receiver values. Failed fits remain failures; scoring happens only
after the fit and forecast artifacts close.
