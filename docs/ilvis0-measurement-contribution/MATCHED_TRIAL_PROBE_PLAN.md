# Check value-only arithmetic on saved aircraft fits

Use three saved aircraft tasks from the closed wider-arithmetic preflight.
Take the IMU8 zero-field disc endpoint and the correction reconstructed
from its saved residual and Jacobian. Take one endpoint each from the
passing specified-field globe on IMU8 and specified-field disc on IMU21.
These cases cover the troublesome disc fit, a passing control and the
fourth matched candidate. Preserve the original stopping outcomes.

At each of the four bound parameter vectors evaluate one full wider tangent
and one wider value-only calculation. Require exact agreement in positions,
coordinate residuals, weighted residuals and packet-boundary counts. Require
the full wider calculation to reproduce the saved endpoint residuals and
the saved cost of the disc correction. Time the calls separately using
process CPU time, excluding setup, compilation and saving. The timing check
describes these points. It does not certify an entire faster fit.

Freeze the original training packets, onboard training positions, clock,
weights, calibration bounds and compiler environment. Leave later positions
out of the study inputs. Allow three tasks, eight native calls in total,
three workers with one numerical thread each, and a 15-minute cooperative
wall limit. Charge each call before execution. No optimizer starts, new
forecasts or Earth-model decisions are allowed.

[Parent preflight results](MATCHED_OBSERVED_NUMERICAL_RESULT.md).
