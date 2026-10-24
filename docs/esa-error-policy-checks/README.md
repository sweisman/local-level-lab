# Receiver-error weighting checks

**All 21 policy checks and 55 supporting covariance checks pass.** The
[working policy](../ESA_ERROR_POLICY.md) retains the receiver's complete
north/east/up covariance and tests two stated correlation assumptions.

The checks verify cross-axis terms and height direction, irregular timestamps,
invalid covariance rejection, unchanged input measurements and independence
from gyro or preferred-model metadata. Dense and structured calculations agree
for a 27-column matrix, including a zero column. Dense requests have an explicit
size cap to prevent accidental whole-record allocation.

Source and environment bindings were written before the final test run.
The exact 14 source files, test report and receipt are retained through the
[shared reproducibility archive](../REPRODUCIBILITY.md), under
`data/ilvis0-source-point-development/esa-error-policy-checks-20261023`.

This verifies software for the declared weighting assumptions. It does not
calibrate receiver accuracy, select an interval or fit any flight. The original
zero-eligible inventory and all protected confirmation groups are unchanged.

To rerun the software checks in the matching environment:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 4 -- ~/venv/bin/python -m pytest -q analysis/tests/test_airquantumgrav_error_policy.py analysis/tests/test_ilvis0_structured_covariance.py analysis/tests/test_ilvis0_error_model.py
```

[Working assumptions](../ESA_ERROR_POLICY.md) · [Next analyses](../NEXT_STEPS.md).
