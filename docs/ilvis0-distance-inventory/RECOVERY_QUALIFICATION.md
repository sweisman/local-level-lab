# Execution and recovery check

The prepared study has 232 immutable file tasks, one worker and one numerical
thread, a four-hour wall limit, zero model evaluations and zero protected
flight reads. Its frozen manifest is SHA-256
`25d41f65d74b32ffe27bf7c04b32dbb54bba96c497443eef15d977b496c214f6`.
The source corpus totals 1.37 GiB compressed; the largest file is 7.4 MiB.

The shared worker and task-continuation recovery tests passed 24/24 with
one thread. An interrupted task retains its charge; the original run resumes
only unstarted tasks. After closure, the separately charged task-continuation
protocol can recover unfinished technical work without rewriting sealed
results. Repeating this command checks the existing manifest and journals
before scheduling anything:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  ~/venv/bin/python -m lll.studies run data/ilvis0-distance-inventory-20261116 \
  --reserved-threads 0
```
