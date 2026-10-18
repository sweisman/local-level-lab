# Measurement dependencies in the current comparison

Two observational streams enter the archival fit: Group-4 inertial increments
and Group-10001 receiver coordinates. Group-1 fused navigation is used for
decoder validation and motion screening; it does not supply the fitted attitude,
angular-rate observations or position residuals.

| Step | Measurements or assumptions used | What a contribution test must preserve or replace explicitly |
|---|---|---|
| Selection | Original completeness rules, receiver speed/trajectory and documented motion screening | Keep the saved 53 intervals fixed; never select favorable model residuals. |
| Initial position and velocity | Straight-line fits to the first ten seconds of receiver latitude, longitude and height; candidate coordinate metric converts rates to velocity | Dropping a coordinate from the objective does not remove its initialization influence. |
| Initial tilt | Mean measured accelerometer specific force over up to the first 2,000 IMU samples | An acceleration-free control needs an independent tilt constraint or must report the lost identifiability. |
| Initial yaw | Course derived from the receiver-initialized horizontal velocity | Course is not measured aircraft heading; nuisance attitude freedom must remain explicit. |
| Attitude propagation | Recorded gyro increments, allowed gyro calibration, transport and background-field terms | A gyro-free control needs a separately stated orientation model; fused Group-1 attitude cannot supply independent gyro evidence. |
| Velocity and position propagation | Recorded accelerometer increments projected through reconstructed attitude, gravity, candidate geometry and declared corrections | Gyro and acceleration contributions interact; their effects need not divide into independent percentages. |
| Objective | Predicted minus measured receiver latitude, longitude and ellipsoid height, jointly whitened | Coordinate subsets require their marginal covariance before whitening. |
| Covariance and physical error summaries | Shared receiver-error assumptions and a common WGS84 conversion | Separate the observation weights and reporting metric from the physical model being tested. |
| Numerical checks | Fresh predictions, full nuisance Jacobians, physical position stability and required repeats | Lost rank or an unconstrained direction after ablation is a result to report, not a reason to delete active columns. |

The production evidence gate remains separate from these development comparisons.
The original observations, selected intervals and three physical models stay
frozen. The first adapter changes only the receiver-coordinate objective; it
does not change the upstream measurement dependencies in this table.

Implementation references: [initialization](../../analysis/lll/ilvis0_corpus_modeling.py),
[native prediction and whitening](../../analysis/lll/ilvis0_shape.py),
[receiver covariance](../../analysis/lll/ilvis0_gps_sensitivity.py),
[coordinate projection](../../analysis/lll/ilvis0_observation_projection.py).
