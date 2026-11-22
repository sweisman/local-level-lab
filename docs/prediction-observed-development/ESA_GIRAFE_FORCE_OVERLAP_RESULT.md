# Two instruments track the same force changes with a persistent offset

On the eight matched windows from the ESA development flight, GIRAFE
read **26–29 mm/s² lower on average** than iMAR. Their force magnitudes
moved together. The correlation on the eight later supports in each
setting ranged from 0.982 to nearly 1.000. The median disagreement after
subtracting each setting's own mean difference was **1.8 mm/s² RMS**.
The subtraction describes agreement on these observations. Predicting
that difference on a fresh window requires a separate check.

| Windows and averaging width | Median RMS difference | Median centered RMS | Mean GIRAFE minus iMAR range |
| --- | ---: | ---: | ---: |
| Straight-course, 11 receiver reports | 27.37 mm/s² | 2.69 mm/s² | −28.78 to −25.65 mm/s² |
| Straight-course, 25 receiver reports | 26.96 mm/s² | 1.30 mm/s² | −29.06 to −26.38 mm/s² |
| Turning, 11 receiver reports | 28.02 mm/s² | 1.89 mm/s² | −28.75 to −26.29 mm/s² |
| Turning, 25 receiver reports | 27.49 mm/s² | 1.36 mm/s² | −27.74 to −26.28 mm/s² |

The table uses the declared UTC conversion and moves the measured iMAR
force to GIRAFE's documented location. The correction slightly raises
uncentered RMS in all 16 later settings. Shifting GIRAFE's clock by
±0.1 s changes the median centered RMS to 1.85–1.99 mm/s². A shift of
±0.5 s increases it to 2.72–3.40 mm/s². The main comparison keeps the
logged alignment and uses the original sensor scales.

The result gives a separate measurement of the scale of force changes
on one aircraft. The constant difference could arise in either sensor
or in how their readings were processed. Three-axis force magnitude
leaves heading uncertainty open. A direct comparison with the predicted
globe–disc force contrast still needs to account for the observed
offsets, time correlation and receiver error.

All eight tasks passed. The ledger verifies 957,720 iMAR intervals and
no new calibration fit or reserved-flight access. [Frozen design](ESA_GIRAFE_FORCE_OVERLAP_PLAN.md) ·
[Matched values and charges](esa-girafe-force-overlap-result.json) ·
[Original-file inventory](../external-imu-data/ESA_GIRAFE_187.md)

To verify the local result, restore the closed
`data/esa-girafe-force-overlap-v1` study and run from the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_girafe_force_overlap report
```
