# Four-setting known-calibration noise benchmark

The [construction gate](construction-qualification/README.md) passes 27 checks.
This execution uses those same shared construction, native noise and summary
components. It is a benchmark of declared assumptions, not a fitting campaign.

| Duration | Queries | Earlier / later | IMU packets per case | Cases |
|---|---:|---:|---:|---:|
| 120 seconds | 119 | 79 / 40 | 36,000 | Increment and sampled-rate laws |
| 1,200 seconds | 1,200 | 800 / 400 | 360,000 | Increment and sampled-rate laws |

Use the known northern, fast-turning, climbing nominal trajectory. Known sensor
bias/gain, lever arm, latency and initial state are supplied. No noisy data are
drawn. Nominal future geometry sets the oracle metric and covariance transforms;
it is not available to the actual prediction protocol. Future receiver noise
loadings stop at the earlier boundary for the physical-position target.

The shared study engine has four immutable tasks, two workers with one numerical
thread each, and a two-hour cooperative wall allowance. Reserve capacity for
other running jobs within the four-thread total. Permit one bridge compilation
per worker. Root native-call and packet-visit allowances are both 794,638: one
full step per packet and at most one extra partial step per query. Unused
prepayment is retained. Construction permits 794,642 generated samples and
792,000 constructed intervals in total; summary work covers 880 later epochs.
Each covariance operator has a 64 MiB storage cap. There are zero optimizer
starts, noise draws, original-recording reads or protected-data reads.

Save every input binding, compiler/cache identity, construction and native-work
journal, nominal and integrated query means, marginal covariance curve and
summary. Report completed calculations separately from whether their expected
squared error exceeds the unchanged 10 m horizontal / 30 m height RMS screen.
The square root of an expected squared RMS is not an expected realized RMS.

Passing the execution checks means the benchmark was computed and verified.
It does not qualify nonlinear coverage, declare an aircraft detection, change
the earlier noisy failures or release protected confirmation groups.
