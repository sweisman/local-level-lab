# Independent trajectory-force controls

## Question

Does the proposed acceleration-only diagnostic correctly transform a declared
receiver trajectory into the required specific force under each of the three
physical models, without using gyroscopes or fused navigation?

This is a deterministic software qualification. It does not measure instrument
performance, establish a calibrated likelihood or add flight evidence.

## Independent reference

Generate twenty-one exact epochs over twenty seconds for six declared motion
profiles: stationary, slow, eastbound, northbound, changing direction and climbing
with acceleration. Use both hemispheres across the matrix. Evaluate all three
physical candidates for each truth, preserving comparisons that do not separate.

Reference positions and the north/east/down basis are constructed in Cartesian
coordinates from independent WGS84 ellipsoid/disc equations. Second-order scalar
jets differentiate those equations. Reference specific force follows Cartesian
acceleration plus Coriolis, with apparent gravity declared explicitly. No
production geographic kinematics or force helper generates the reference.

The adapter instead differentiates the candidate's coordinate metric to obtain
local velocity and its component derivative, calculates transport, and calls the
qualified force helper. Check its true-model velocity, acceleration, transport
and force against the independent reference. Two distinct changing body attitudes
must give the same acceleration-magnitude residual. No gyro stream is generated
or supplied to the adapter.

This fixes the background rate only to test the declared models; it is not a free
field measurement. Gravity is an explicit 9.81 m/s² software assumption. It is
apparent gravity, including the usual centrifugal contribution for the rotating
case; it must not be mistaken for an independent raw gravitational observation.

## Finite scope and acceptance

| Work | Maximum |
|---|---:|
| Diagnostic identities | 18 |
| Epochs per identity | 21 |
| Candidate receiver-force evaluations | 1,134 |
| Scalar magnitude comparisons, two attitudes | 2,268 |
| Optimizer starts / native calls / original reads | 0 / 0 / 0 |
| Numerical threads | 4 total, one worker |
| Runtime | 60 seconds |
| Retries | 0 |

Each true-model check must have maximum component error below 10⁻⁸ m/s for
velocity, 10⁻⁹ m/s² for local acceleration and specific force, and 10⁻¹² rad/s
for transport. Magnitude residual and two-attitude agreement must be below
10⁻⁹ m/s². Stationary controls must retain the indistinguishable force magnitudes;
incorrect-model cases are reported without requiring a positive distinction.

Freeze source/environment hashes, the complete task list and limits before the
batch. Charge each identity before evaluation and save all returned outcomes.
The completed batch cannot restart. A failed check blocks recorded-data use and
is retained for diagnosis.

## Files and subsequent gate

- `analysis/lll/ilvis0_receiver_force.py`: candidate coordinate/force adapter.
- `analysis/tests/ilvis0_channel_reference.py`: independent Cartesian reference.
- `analysis/tests/test_ilvis0_receiver_force.py`: focused adapter/reference checks.
- `analysis/tests/ilvis0_channel_trajectory_worker.py`: finite freeze, execution
  and saved-only publication.

After this force calculation passes, receiver-trajectory differentiation and its
temporal uncertainty still need qualification. Calibration, averaging of raw
increments, synchronization and initialization must be declared before a finite
recorded-data comparison. Passing these exact-trajectory controls alone does not
authorize that comparison or change the main 53-stretch findings.
