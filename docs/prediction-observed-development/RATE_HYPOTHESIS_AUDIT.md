# What the saved ESA rate samples say about integration

The ESA iMAR file reports angular rates and accelerations. The analysis
constructs increments between adjacent reports using the average of the two
values. This saved-data check recomputed those increments from all **360,029**
original rate samples in development recording 187. The stored increments
match that calculation exactly. The training cutoff is after 239,867 of the
360,028 intervals. Intervals are about 3.333 milliseconds long, with no
interval above 3.334 milliseconds in this saved stretch.

If each rate instead applies to the *preceding* interval, the difference from
the current average-value construction, accumulated over the full interval,
is −0.0000030, +0.0000144, −0.0000082 radians on the three gyro axes. Assuming
it applies to the *following* interval gives the opposite signs. The largest
absolute final gyro-axis difference is about **0.00082°**. The largest final
accelerometer-derived velocity difference is **0.00684 m/s**. These are signed
component sums; rapidly changing contributions cancel. The sum of absolute
per-interval differences is much larger, so the small final sums do **not**
bound a reconstructed aircraft position.

This check verifies the saved-data construction, but it cannot tell which
sampling convention the instrument used. Rotation composition, changing
force direction, filtering and coning/sculling may make navigation results
sensitive even when component sums nearly cancel. A frozen, matched native
propagation at fixed fitted parameters [now measures that sensitivity](RATE_PROPAGATION_V2_RESULT.md):
the alternative later trajectories differ by 19–43 m horizontal RMS.
Choosing an instrument interpretation still requires independent evidence or
a validated training-only selection rule. No model was refitted and no
reserved flight was opened in this component check.

The [plan](RATE_HYPOTHESIS_PLAN.md), [machine-readable result](rate-hypothesis-audit.json),
and [ESA rate adapter](../../analysis/lll/airquantumgrav_increments.py)
record the exact question and arithmetic. This remains a development
diagnostic, with no Earth-model decision.
