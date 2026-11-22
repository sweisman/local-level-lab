# Accounting for the antenna offset preserves the shape ranking

The globe gives lower force-direction error than the disc in **all 48
comparisons** after accounting for the distance from the inertial
measurement unit to the receiver antenna. All 16 comparisons with zero
background field in both shapes still favor the globe. These are eight
windows from one development flight.

When the aircraft turns, the two points move differently. We used the
published iMAR-to-antenna offset of **2.12 m** and the logged gyro to
estimate the effect before comparing the pair angles. The campaign
estimated the offset using its inertial and receiver data, so the replay
tests one documented value. It does not fit the offset or use the
campaign's fused attitude as a reference. [Campaign methods and Table 1](https://essd.copernicus.org/articles/17/1667/2025/#section2)

| Windows and field assumption | Globe median RMS | Disc median RMS | Smallest paired gap |
| --- | ---: | ---: | ---: |
| Straight-course, zero field in both | 0.1160° | 0.1565° | 0.0215° |
| Straight-course, specified field retained | 0.0042° | 0.0524° | 0.0162° |
| Straight-course, specified field removed from gyro | 0.1160° | 0.1563° | 0.0224° |
| Turning, zero field in both | 0.1140° | 0.1432° | 0.0194° |
| Turning, specified field retained | 0.0030° | 0.0455° | 0.0312° |
| Turning, specified field removed from gyro | 0.1144° | 0.1436° | 0.0194° |

The offset changes the measured angle sets by up to **0.0880° RMS**.
With the model predictions held fixed, the smallest RMS change that
could tie a corrected comparison is **0.0115°** in the retained-field
case. It is **0.0510°** in the zero-field case. These distances describe
the saved angle scores. They do not measure the real size or correlation
of remaining instrument and receiver errors.

All eight tasks reproduced the uncorrected directions before comparing
the corrected angles. They replayed 957,720 packet intervals with no
calibration fit or reserved-flight access. [Frozen design](ESA_DIRECTION_LEVER_ARM_PLAN.md) ·
[All corrected angles and scores](esa-direction-lever-arm-result.json)

## Verify the tables

The following command checks the three saved reports and recomputes the
tables using standard Python. It needs no flight files or archive catalog.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_evidence
```

With the closed `data/esa-direction-lever-arm-v1` study restored, run
`python -m lll.esa_direction_lever_arm report` through the one-thread
numerical guard to verify the original result ledger.
