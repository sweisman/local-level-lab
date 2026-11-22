# Execution and recovery check

The prepared manifest SHA-256 is
`864df53ae28778d5b29cfcc115961d2d74ffcbcf90e361e5bea76dfbc58adbb7`.
It binds 29 original source hashes and candidate identities, the one-variable
screening policy, source/environment versions, one worker and thread, a
two-hour cooperative limit and zero Earth-model evaluations.

All **52/52** focused selector, adapter, parser and shared recovery checks
passed. The shared suite exercises interrupted task continuation, sealed
result reuse, charge preservation, changed-source rejection and duplicate
owner rejection. The idempotent entry point verifies frozen evidence and
journals before scheduling permitted unfinished work:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  ~/venv/bin/python -m lll.studies run data/ilvis0-alignment-ablation-20261116 \
  --reserved-threads 0
```

This qualifies technical execution, not the scientific use of misaligned
fused-navigation motion values.
