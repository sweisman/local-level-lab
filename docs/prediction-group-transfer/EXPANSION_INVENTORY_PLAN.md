# Remaining NASA prediction groups: metadata inventory

This inventory prepares a possible group-level prediction study. It makes no
new fit, coverage claim or Earth-model decision. The earlier four-group
transfer check is preserved unchanged.

Use the frozen 53-stretch selection and the conservative provenance ledger.
Exclude the three groups used in the original prediction pilot and the four
groups used in the first transfer check. For each other group, select the
longest eligible stretch by recorded duration, breaking a tie by segment ID.
Only segment identity, source hash, filename, times, duration, IMU type,
latitude, course, speed and provenance group may enter. Ignore every model
outcome, gyro value and residual. Verify source hashes and prior group IDs;
reject missing, duplicate or inconsistent metadata.

Record every remaining group and its representative in a CSV with hashes of
the four input tables and selector source. This is a **candidate inventory**,
not authorization to run fits. Before any subsequent observed calculation,
freeze the error-law rule, full model/case grid, earlier/later split, starts,
numerical limits, adequacy screen, group-level scoring, source/environment
hashes and task-level recovery. The seven reserved ESA groups remain closed.
