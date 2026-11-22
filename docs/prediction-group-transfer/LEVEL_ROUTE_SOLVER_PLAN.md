# Level-route numerical stress control

The [complete-vector path check](OBSERVED_PAIR_PATH_RESULT.md) found a
near-flat training-cost connection with changing forecasts on one recorded
inner cut. This separate generated-data control asks whether level-flight
route geometry alone can reproduce such numerical forecast disagreement.
It does not use recorded aircraft increments, receiver positions or the
seven reserved ESA confirmation groups.

Construct two matched 120-second histories with the existing independent
truth generator: one straight route and one turning route, both at 55° N,
200 Hz, level height, specified-field globe truth, identical declared
increment-noise seed and Z-axis gyro calibration near its permitted boundary.
Use 119 one-second receiver reports. Fit the first 79 and save the continuous
40-report forecast before comparing it with generated truth. The two route
recipes differ only in route shape. The exact generated noise is an assumption,
not a measurement of either archival instrument.

For each route, run SciPy TRF and the custom bounded trust-region optimizer
from zero and one preregistered perturbed start: **eight fit identities**.
Retain all 26 active calibration directions and the same physical bounds.
First qualify a separate 10-second one-task real-worker preflight. Freeze
source, inputs, environment, selections, starting points, one-thread-per-worker
allocation and task-level reboot recovery. Each full fit has at most 200
evaluations, 40,104 native calls and 251,034,903 packet visits; totals are at
most **320,832 calls and 2,008,279,224 packet visits**. Use four one-thread
workers, no retries, and a six-hour cooperative wall cap. Charge before work
and preserve every failure.

The preregistered numerical agreement check is: all eight fits pass their
unchanged final stopping checks; within each route all four training costs
span at most 0.01 and all four later paths differ by at most 0.1 m. Report
generated-truth forecast errors separately. A failure is a retained result
and prompts diagnosis; it does not authorize new starts or a relaxed gate.
A pass qualifies only these generated route controls. It cannot establish
aircraft prediction accuracy, a calibrated error law, global optimality or
an Earth-model detection. Preserve all original recorded-fit labels.
