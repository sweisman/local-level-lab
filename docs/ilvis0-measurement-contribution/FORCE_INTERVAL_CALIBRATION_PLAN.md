# Test both ends of the measured force interval under one gain

Use all 991 original windows, both packet clocks and the four shape and field
candidates. Compare the measured accelerometer bounds with the saved
predicted force bounds for onboard and [carrier-phase motion](GPS_CARRIER_FORCE_RESULT.md).
Use the same nonnegative gain range of 0–15% as the
[previous lower-bound check](MATCHED_FORCE_GAIN_RESULT.md). This gain is
shared across the axes and all windows within one recording and candidate.

If one gain makes the measured and scaled predicted intervals overlap in
every training window, retain the interval of such gains and use its smallest
value. Otherwise find the gain that minimizes the maximum separation between
the measured and scaled predicted intervals. Give an upper and lower bound
on that minimum. The two possible gap types move in opposite directions as
gain increases, so their crossing can be bracketed by bisection. This is a
uniform force gap in measured units. It gives no estimate of the component
due to receiver error, calibration, attitude or motion.

Use the training gain and gap allowance unchanged on later windows. Report
the additional gap required at the fixed gain and the number of later cases
outside the training allowance. Run separate profiles for each receiver
motion input and a profile requiring the same gain and allowance to cover
both inputs. The joint case is a sensitivity check across two possible
paths that share many errors. Overlap is a necessary check on the saved
intervals. It does not establish one trajectory or one time offset that
satisfies the entire recording.

Limit this calculation to 24 closed profiles, 52 bisection steps per profile
and one numerical thread. Read only saved force bounds. Use zero position
solves, inertial fits or gyro observations. Freeze source and inputs before
running, then verify the saved result by exact replay.
