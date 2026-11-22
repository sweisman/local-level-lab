# A shared calibration removes the small source-specific reversal

The globe had lower later direction error in **all 18 comparisons** when
each shape used one calibration and starting rotation trained jointly on
the receiver export, GPS Doppler and GLONASS Doppler. All **nine additional
comparisons** in the 11-report retained-field setting also favored the
globe when one velocity source at a time was left out of training.

The narrowest differences remain in the 11-report retained-field setting.
The table gives disc minus globe angular RMS, with positive values favoring
the globe. All three sources are used for scoring in each row.

| Earlier velocity sources | Later receiver export | Later GPS Doppler | Later GLONASS Doppler |
| --- | ---: | ---: | ---: |
| All three | +0.00537° | +0.00486° | +0.00245° |
| GPS and GLONASS | +0.00416° | +0.00373° | +0.00174° |
| Export and GLONASS | +0.00368° | +0.00325° | +0.00125° |
| Export and GPS | +0.00563° | +0.00496° | +0.00171° |

With all three sources in training, the retained-field margin grows to
**0.0478–0.0503°** at 25-report averaging. The matched zero-field margins
across both widths are **0.106–0.113°**. These differences are descriptive.
The smallest gap across all pooled and two-source checks is only 0.00125°.
A change smaller than about 0.00062° RMS to each candidate's later angular
errors would suffice to preserve that ranking at the fixed fits. There is
no verified direction-error bound at that scale.

All **18 fits** passed the unchanged exact gradient limit, with a largest
final gradient of 5.83 × 10⁻¹¹. Each fit reached at least one working bound.
The calculation used 49 earlier derivative evaluations and 18 later
value-only replays. The single-source GLONASS reversal remains in its
original report. The new result addresses it under equal-source weighting
and the specified two-source alternatives. It does not establish calibration
for other flights or remove common errors in products from the same antenna.

No full inertial fit or original data-file read was used. All seven
reserved groups and the original 120 position holdouts stayed outside
this comparison.

## Reproduce the result

With the closed `data/esa-direction-pooled-calibration-v1` study restored,
verify and regenerate the report from saved evidence without refitting.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_pooled_calibration report
```

[Frozen design](ESA_DIRECTION_POOLED_CALIBRATION_PLAN.md) ·
[All 18 fits and 27 paired later scores](esa-direction-pooled-calibration-result.json)
