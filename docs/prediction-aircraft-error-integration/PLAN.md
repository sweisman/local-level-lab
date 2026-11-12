# Generated aircraft uncertainty: finite integration matrix

This study checks whether the complete generated-aircraft fit, two conditional
uncertainty targets and withheld scoring operate together under the planned
case variations. It is a technical gate. Two-second recordings and one noise
seed cannot establish uncertainty coverage, Earth-model selection or archival
instrument behavior.

## Frozen case set

Use exactly 48 starts: three generating physical models, two upstream
processing cases, two synthetic IMU input-error laws (increment and sampled
rate), two sensor-calibration cases (interior and Z gyro gain/bias at the
declared bounds), and two 200 Hz clock inputs. One clock input has exact 5 ms
logged intervals; the other has a declared 0.4 ms, 19-cycle packet-header
disturbance while retaining the same nominally integrated gyro and
accelerometer increments. Each start uses noise seed 71, two seconds of
generated data, nine receiver epochs, six earlier epochs and three withheld
epochs. Fit start 0 has at most eight evaluations. All cases use the same
declared receiver policy and original physical fitting bounds.

Each candidate is fitted to its own independently generated physical truth;
this study tests the pipeline, not discrimination between candidate models.
Save the fitted forecast and both earlier-only fixed-law conditional error
targets before generating withheld physical truth or later receiver reports.
The later receiver draw is separately charged. Preserve the numerical
convergence result, physical-position accuracy, per-axis nominal marginal
coverage and calibration-status abstention for every case. A completed
pipeline check must never be reported as a converged fit or calibrated
confidence claim.

## Work and recovery

Use the shared `lll.studies` lifecycle, four single-thread workers and a
cooperative 30-minute study ceiling. Before launch, bind source and numerical
environment hashes, passing local software qualification and the existing
task-level reboot/interruption recovery qualification. Each case has ceilings
of 2,000 native calls and 20,000 packet-query visits; these exceed the
conservative 1,057-call and 15,400-visit calculation from 400 packets, six
earlier queries, nine total queries, two covariance extensions and eight fit
evaluations. Construction is charged separately: 400 intervals, 416 generated
samples, and the exact law-specific random-variate count plus 60 for the full
receiver report. Save actual attempted work and failures; never reset a
completed task or enlarge this allowance.

No observed aircraft recording or protected ESA confirmation group is read.
The next scientific gate is an independently qualified training-only error-law
estimator and a substantially longer, independently seeded coverage study.

The versioned adapter provides `request`, `recovery-request` and `prepare`
commands through `python -m lll.prediction_aircraft_error_integration`. The
software request must precede its JUnit test report. The recovery request
binds the existing task-continuation checks to the same runtime environment.
Preparation rejects either missing qualification and writes an immutable
definition; execution then uses the shared study runner and the saved
definition. Reports must verify every task and source hash before publication.
