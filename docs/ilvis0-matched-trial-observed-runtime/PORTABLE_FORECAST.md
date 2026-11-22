# Verify the forecast from the saved refit

The [isolated training fit](refit-evidence/README.md) matched the recorded
control byte for byte. The original replay stopped at its wall limit before
forecasting. This separate calculation holds the fitted parameters fixed and
propagates the same 133,680 inertial packets to the original 668 timestamps,
including 223 after training. Later receiver positions are absent from the
worker inputs. The expected forecast digest is frozen before execution. A pass
requires exact equality of the forecast bytes and the native builds used.

The allowance is one task, one native call, zero fit starts, one numerical
thread and a cooperative ten-minute wall limit. An interruption before a
recorded start can continue within the original allowance. A recorded technical
interruption can recover once under the qualified shared task recovery procedure
with a separate identical allowance. A sealed outcome remains final.

From the repository root, use the extracted package and prepared working
directory from the [refit instructions](PORTABLE_REFIT.md). Preparation also
checks the published refit evidence. Run:

```sh
refit_dir=data/ilvis0-nasa-portable-refit-v1-20261118
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_portable_forecast prepare "$refit_dir"
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_portable_forecast run "$refit_dir"
```

This verifies numerical reproducibility of a single recorded forecast on the
pinned host. Assessment of aircraft prediction accuracy is a separate study.
