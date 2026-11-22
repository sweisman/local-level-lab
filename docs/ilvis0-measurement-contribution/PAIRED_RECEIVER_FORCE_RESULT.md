# Receiver choice matters at the scale of the smaller force gaps

Both receivers accepted the 30-second window at **339 of 490** saved
target times across eleven survey legs. All 339 windows passed the
common-epoch check. The remaining 151 keep their original width
dispositions. The calculation uses paired receiver measurements and no
inertial data.

| Trajectory order | Median leg's 95th-percentile force difference | Largest force difference | Later gaps in the two calibration pilots |
|---|---:|---:|---:|
| Quadratic | 0.00169 m/s² | 0.00455 m/s² | 0.0416–0.0535 m/s² |
| Fourth-degree | 0.00261 m/s² | 0.00890 m/s² | 0.00288–0.00570 m/s² |

For each leg, the percentile uses the largest of the four candidates'
95th-percentile absolute force differences. The largest difference is
over every candidate and supported window. The calibration gaps come
from a separate two-recording study with different time supports and
supply a scale comparison.

The quadratic receiver differences were well below the remaining
quadratic calibration gaps. The fourth-degree differences reached the
scale of the later fourth-degree gaps. This shows why a small gap under
the higher-order trajectory is sensitive to receiver motion. It does
not estimate the absolute error of either receiver. The signals can
share satellite and processing errors, and distinct antenna positions
can add real motion to the differences.

The [frozen calculation](PAIRED_RECEIVER_FORCE_PLAN.md) preserves all
eleven pair identities and original target decisions. It completed
43,392 force quadrature evaluations and 1,356 centre kinematic
evaluations, with zero position solves and zero inertial fits. The force
comparison remains diagnostic and supplies no calibrated shape decision.

[Per-window results](paired-receiver-force-windows.json.gz) ·
[All eleven pair summaries](paired-receiver-force-receipt.json).

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_paired_receiver_force replay
```
