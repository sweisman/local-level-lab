# Recover the unstarted IMU21 zero-field disc forecast

The [sealed preflight](MATCHED_OBSERVED_NUMERICAL_RESULT.md) contains one
unstarted task. It is the IMU21 zero-field disc forecast from stretch
`2791235ca0b11b1ef4386e21`. The IMU8 zero-field disc spent 30 evaluations
and failed stopping. Keep that completed outcome and all six forecasts.

Restore the exact archived preflight source and input versions into an
isolated recovery workspace. Verify the terminal receipt, original
charge journals, input hashes, source hashes and numerical environment.
Use the existing qualified task-continuation workflow. The first stage
contains the one untouched identity, with the original zero start,
nominal clock, weighting, calibration bounds and solver. It has exactly
30 training evaluations and one optional forecast. Preserve the original
forecast-before-scoring order and prefix and stopping checks.

Use one numerical thread and a 65-minute overall cooperative limit.
Allow at most two charged starts for the identity, with the second
available only after a recorded technical interruption. A fitted
nonpassing result remains terminal. Start no other model and do not
substitute the current checkout for any frozen source. The retained
source restores include only those dependencies named by the archive
and the recorded recovery qualification.

The allowanced task is expected to take up to about 25 minutes in an
uninterrupted run based on the saved IMU21 tangent timing. Longer elapsed
time may be needed for compilation and recovery. This development
result can fill one missing model slot. The two-recording comparison
still needs the IMU8 zero-field disc and qualified aircraft uncertainty.

From the repository root, use the existing environment. `prepare`
verifies and materializes the original evidence, freezes the continuation
and registers the first stage. `resume` verifies the freeze and runs
only pending work. The same command is safe after a technical interruption.
Use `check` to audit recovery readiness against the restored sources.
The main status command shows execution progress for the registered stage.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_matched_unstarted_recovery prepare
env PYTHONPATH=analysis LLL_STATUS_ALLOCATIONS_ONLY=1 ~/venv/bin/python -m lll.ilvis0_matched_unstarted_recovery resume
```
