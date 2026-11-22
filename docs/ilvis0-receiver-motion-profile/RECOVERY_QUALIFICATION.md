# Execution and recovery check

The prepared manifest SHA-256 is
`45231a2830d81e771e7fd45e06c123749f239d740cd47fd573bbaa75c404402c`.
It freezes 29 exact candidate sources, their original hashes and segment IDs,
the method and Python/NumPy/SciPy environment, one worker/thread, a two-hour
cooperative wall limit and zero model evaluations.

The four focused motion/adapter tests and 34 shared study and task-resume
checks passed: **38/38**. The shared checks exercise reboot continuation,
sealed-result reuse, charges, changed-source rejection and duplicate-owner
rejection. The idempotent entry point verifies the frozen manifest and
journals before running only permitted unfinished work:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  ~/venv/bin/python -m lll.studies run data/ilvis0-receiver-motion-profile-20261116 \
  --reserved-threads 0
```

This software check does not validate the physical receiver error model or
grant scientific eligibility to any candidate.
