# Earlier data can correct a shared error scale in the affine control

The whole-path score now includes uncertainty from calibration estimated on
the earlier reports. Its joint covariance matches a separate dense solution.
The calculation still abstains if a calibration direction can change the
later path while remaining invisible during training.

In the fixed affine control, estimating one common variance from the first
12 reports kept the later eight-report score near its nominal 95% inclusion
rate even when the generator multiplied the whole variance by nine.

| Generated condition | Histories | Inside nominal fixed-scale reference | Inside earlier-estimated-scale reference |
|---|---:|---:|---:|
| Nominal variance | 1,024 | 972 (94.9%) | 976 (95.3%) |
| Ninefold common variance | 1,024 | 19 (1.9%) | 971 (94.8%) |
| Ninefold receiver variance after the cut | 1,024 | 38 (3.7%) | 207 (20.2%) |

All three predeclared software checks passed. The last row tests a deliberate
change in error behavior at the cut. An estimate from earlier observations
cannot account for that change under a shared-scale rule.

These are exact affine Gaussian controls without bounds or physical-model
selection. The aircraft still needs matched nonlinear calibration and error
checks, including stability from the earlier to the later period. The new
reference was never applied to the ESA scores and no reserved data were used.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.calibrated_joint_path_control replay
```

[Fixed plan](CALIBRATED_JOINT_SCORE_PLAN.md) · [Frozen inputs](calibrated-joint-score-freeze.json) ·
[All control counts](calibrated-joint-score-result.json)
