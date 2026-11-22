# Physical-Jacobian receiver whitening check

Use the first 120 training receiver epochs of the already opened NASA
development case `bb8061a43b4f14b6262ceda1-outer-0-header_elapsed-1`.
The corresponding raw IMU increments, receiver times and positions come
from its sealed training inputs. No later receiver positions or scoring
inputs are available to this study. The case is chosen for a numerical
software comparison, not an Earth-model decision.

Build the identical `h1_v3_tau60` receiver law twice: the established dense
coordinate covariance and its algebraically equivalent structured form.
At the **zero normalized calibration point**, calculate one native physical
prediction and all 26 calibration derivatives under the specified-field
globe model and header-elapsed clock. Whiten the same raw residual and
Jacobian through both paths. Report the maximum residual, Jacobian, cost and
log-determinant differences. A finite native call is charged before execution.
There is no fitting, start search or change to any saved fit label.

Freeze the parent manifest and copied training-only arrays, all Python and
native source files, runtime environment, one task, one native call, its
exact packet-visit ceiling, one numerical thread and a 15-minute cooperative
wall limit. Require source-bound tests and the existing five-test task-level
recovery qualification. After a verified worker interruption, seal the
original and allow one separately frozen continuation attempt (two charged
attempts total, one technical interruption total, another 15-minute wall
limit and a 5 GiB free-space floor). Sealed failures are not retried.

Passing this check would qualify the dense/structured **physical Jacobian
calculation at one point**. A matched fitted comparison, actual error-law
adequacy and long-recording prediction remain separate gates.
