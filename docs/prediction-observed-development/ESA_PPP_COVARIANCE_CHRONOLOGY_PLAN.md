# Test receiver error covariance across the development flight

The [eight-window difference comparison](ESA_RECEIVER_CONTRAST_COVARIANCE_RESULT.md)
found some predictive benefit from separate GPS receiver terms. The
[raw carrier comparisons](ESA_RAW_PHASE_PPP_TIMESCALE_RESULT.md) gave no
consistent basis for taking raw carrier variation as position uncertainty.
Test the receiver terms more broadly against the already inventoried
GPS position solutions from the one opened ESA flight.

Use the published list of 195 two-minute windows where both alternate
position solutions met the original speed and matched-epoch rules.
Verify the three named source files and the saved window identifiers.
Some archived bins have 119 or 121 matches because their reported
timestamps straddle a window boundary. Fix the target grid at the 120
integer GPS seconds in each window and match at the archived
two-millisecond tolerance. Use the reported velocity for the same
first-order time correction as the raw comparison, with no interpolation.
Keep a window only if all three solutions match all 120 targets. Record
all original identities and every incomplete window. Decide eligibility
using timestamps and the earlier speed selection. Do not use the sign or
size of the differences.

Divide the original 195 windows chronologically before checking
completeness. Train on the first 97, then score the last 98 in four
contiguous batches of 25, 25, 24 and 24. Use the same contrast channels
and three fixed cosine bands as the eight-window comparison. Also fit
the constant coefficient separately to include relative position
offsets. Subtract its six-channel donor mean from donor and test
coefficients. Use the same clipping and ridge for the separate-receiver
law, unrestricted covariance and isotropic reference. Freeze the donor
settings before scoring the later batches. Retain the earlier and later
jobs separately so the same donor settings can be reused after a reboot.

Report Gaussian log scores and standardized squared error for each
law, band and later batch. Compare transfer on the full and constant-free
contrasts. Require at least seven complete donor windows to estimate
the six-channel covariance of the offsets. Treat results as descriptive comparisons of relative error on
one flight. Antenna and common GPS error remain outside the method, and
no reserved recording, original IMU stream or aircraft fit is used.

Freeze one donor task with up to 101 bound calls and 400 steps. After
verifying its sealed settings, freeze the four score batches with up to
`window count + 12` calls and `16 × window count` steps each. Use one
single-thread worker for training and two single-thread workers for
scoring, with a 180-second limit for each stage. Check eligibility in
the archived reference GPS week. Preserve missing-window reasons and
recover only interrupted tasks, with one additional attempt each and a
separate 180-second recovery allowance.
