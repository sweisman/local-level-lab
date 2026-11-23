# Can the reserved flights support matched prediction times?

Check only the earliest timing-verified 20-minute slice in each of the seven
reserved ESA flight groups. Fix the time rule before opening the receiver
exports. From the start of each slice, skip its first second and take the
first 920 receiver reports. Require the last report to precede the end of
the slice by at least one second. The guards are wider than the timing
offset used in the development fits. Require consecutive source indices,
one GPS week and the existing receiver gap limit of 0.75 seconds.

The first 800 reports define the longer training layout. Its final 400
reports define the shorter layout. The next 120 reports are held out in
both. Both layouts have the same last training time and first prediction
time. This tests support for comparing training lengths against identical
observations. The 400/120 development flight did not compare these two
placements. Neither layout is approved for fitting or scoring
by this check.

Use the exact receipt-bound receiver file for each verified slice. Check
file size and SHA-256. Store group, file, inclusive positions in the source
sequence, time ranges and hashes of the time lists. Receiver coordinates
and other measurement values stay out of the result. Read at most seven
receiver files, no raw inertial values and no model outcomes. A failed
window stays in the ledger with its reason. No alternate window may be
substituted. The method, error model, adequacy and final selection remain
separate gates.

From the repository root, run the two commands in order. The first binds
the fixed scope. The second checks the exact receiver files where locally
available, using one worker and one thread.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_confirmation_queries freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_confirmation_queries check
```
