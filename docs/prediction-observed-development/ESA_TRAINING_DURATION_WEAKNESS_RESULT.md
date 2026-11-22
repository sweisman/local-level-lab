# More earlier observations strengthen the weak calibration direction

The [saved comparison](ESA_TRAINING_DURATION_WEAKNESS_PLAN.md) uses two
rotating-globe fits from the same opened ESA flight. One fit saw the first 400
receiver reports; the other saw the first 600. The shorter training rows are
an exact prefix of the longer set. Candidate, start, recipe and source
identity and declared error-law parameters match. Both IMU error laws give
nearly identical results.

| Local training measure | First 400 reports | First 600 reports |
| --- | ---: | ---: |
| Weakest singular value | 0.511 | 1.204 |
| Weakest / strongest singular value | 0.0000116 | 0.0000269 |
| Z gyro-bias conditional column norm | Baseline | **3.23× baseline** |
| Vertical accelerometer-bias conditional column norm | Baseline | **2.40× baseline** |

The GNSS-only receiver velocities show that the aircraft also changed motion
through this interval:

| Part of training | Ground course, first → last | Median ground speed | Height change |
| --- | ---: | ---: | ---: |
| First 400 reports | 115.9° → 75.5° | 71.5 m/s | +1,354 m |
| Added 200 reports | 75.5° → 64.9° | 73.5 m/s | +643 m |

Ground course is the direction of travel, not the aircraft's nose heading.
This flight both changed course and climbed; the saved comparison cannot
assign the information gain to elapsed time, course change or climb alone.

At 400 reports, Z gyro bias accounts for about 0.95 of the weakest local
direction's unit-vector magnitude. At 600, its loading is about 0.075 and
timing offset and lever arm become the two largest components. Neither of
these two fitted biases is at a permitted bound in either fit.

The squared column norms correspond to local information under the declared
whitened error model. Thus this flight's added 200 earlier reports **do help**
constrain the local calibration ambiguity. This does not mean that duration alone solves the
prediction problem: the [saved longer forecast](TRAINING_SPLIT_EXTENSION_RESULT.md)
from the 600-report fit loses height coverage later in the flight. The
Jacobian is local to each fitted solution, and the two fits share their first
400 reports. They are not independent replications or a calibrated uncertainty
test. The scientific decision remains **abstain**.

As a check on the changed fitted parameters, the first 400 rows of the
600-report fit's own sequentially whitened Jacobian were compared with all
600 rows at that **same** fit. The added rows increase the conditional Z
gyro-bias column norm 3.23-fold and the vertical accelerometer-bias norm
2.41-fold. This confirms that the new training observations add local
sensitivity within the fixed calculation; it still does not isolate course,
climb or elapsed time as the cause.

The [byte-reproducible report](esa-training-duration-weakness.json) retains
both error laws, fit hashes, source and manifest hashes, full local loadings,
and the conditional column norms. It required no new fit and opened none of
the seven reserved ESA groups.
