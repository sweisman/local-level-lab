# Generated aircraft uncertainty: integration result

The frozen 48-case technical study completed. All 48 cases passed the data-path
checks, with no execution errors. The cases covered three generating models,
two processing assumptions, two synthetic IMU error forms, two calibration
states and two logged-clock inputs. Each case used the same two-second history
and one predeclared noise seed. The [plan](PLAN.md) defines the matrix and its
finite work limits.

The source-bound software suite passed 38 tests; the separate task-recovery
suite passed five. The saved study completion records 48/48 charged identities,
48/48 completed results, 96,000/96,000 reserved native calls, and no active
worker locks. Every case saved both the physical-position and future-receiver
uncertainty targets before scoring withheld data. The point-rate and increment
cases made their separately charged future receiver draws: 4,914 and 7,308
normal variates per case, respectively.

**Scientific result: abstain in every case.** None of the 48 short fits passed
the numerical convergence check or the physical prediction check. The
technical pass means that the full pipeline ran and preserved the required
artifacts and accounting. It does not qualify the error law, uncertainty
coverage, physical accuracy or a choice among Earth models. No recorded
aircraft measurements or reserved confirmation groups were used.

The next gate is a separate, longer, independently seeded known-answer study
with a training-only error-law estimator, predeclared coverage criteria and
sufficient numerical allowance to test actual fit convergence. Its method and
limits must be frozen before it reads withheld outcomes.

Evidence: `data/prediction-aircraft-error-integration-20261111/` contains the
immutable study definition, source/environment manifest, task journals,
hashed results and completion record. The qualification reports and requests
are in [`qualification/`](qualification/).
