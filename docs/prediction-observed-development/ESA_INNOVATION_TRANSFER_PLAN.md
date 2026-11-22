# Test how earlier forecast errors transfer to the later ESA window

Reuse the two sealed 120-report holdouts on development recording 187,
under both IMU error descriptions. Use the archived complete factors
to remove the covariance assumed by each forecast. Require the
resulting energy to match the original joint score.

For each window, report the share of score energy in each set of 30
consecutive epochs, the fraction in the three largest epochs per
channel, the signed means and the adjacent-epoch correlation. Apply
the same calculation to the signed position errors in metres.

Estimate three working score covariances from the earlier holdout.
Use one common scale, separate channel scales and a full three-channel
covariance, each with forecast error centred at its predicted value of
zero. Save the estimates before scoring the later window. Compare
scores without adjusting the earlier estimates. The two holdouts
belong to one flight. Both are development diagnostics. No score from
the comparison qualifies a range for new aircraft.

Use one numerical thread. The four fixed innovation passes reuse the
original fits, factors and scoring epochs. There are no new native
sweeps, refits or protected-flight reads.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_innovation_transfer freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_innovation_transfer earlier
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_innovation_transfer compare
```
