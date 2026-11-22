# Bind the four repeat-turn inputs before fitting

Use exactly the [four non-overlapping supports](ESA_REPEAT_TURN_RESULT.md).
Take every second receiver report, starting with the second native
report in each support. Decode the earlier 400 receiver observations
and only the clock, sequence and GPS week for the later 120. Hash the
original receiver file while extracting these fields. Keep the raw
inertial samples through the later queries because the planned forecast
uses IMU motion and predicts the later receiver positions.

Use the same actual-time, linear point-sample integration as the prior
400/120 development study, with 50 ms edge padding, ±10 ms of allowed
fit latency and a 5 ms maximum packet interval. Bound the training
prefix at the first raw point that brackets the last earlier query plus
the latency allowance. Check that earlier weights use only the 400
earlier receiver observations. Bind the raw arrays, constructed
increments, training rows, timestamp layout and training prefix by hash.
Count the archived angular trigger exposures before and after the cut
and during the original 30-second turn block.

One numerical thread, one scan and hash per original, at most 628,000
decoded inertial samples and constructed intervals, four sets of
training receiver weights, zero trajectory fits and zero scoring
positions decoded. Hashes describe reproducible inputs. A later
execution freeze must bind the resumed fit method, both IMU error
descriptions and separate outcome scoring before fitting.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_inputs freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_inputs replay
```
