# How the analysis developed

The **[study index](STUDIES.md)** is the public guide to the investigations: what
each added, which approaches failed, and how the published results progressed.
It links to the preserved reports rather than combining earlier totals with the
current findings.

An **IMU (inertial measurement unit)** records turning and acceleration. The work
began by validating those recorded increments and the separate receiver positions,
then fixing eligible intervals before model comparison. Numerical recovery kept
the same observations and physical bounds while investigating stopping rules,
arithmetic precision, calibration trade-offs and time alignment.

**[Current status](CURRENT_STATUS.md)** gives the verified combined results.
**[The measurement method](METHODOLOGY.md)** explains the comparison.
**[All flight stretches](ilvis0-current-findings-20261015/STRETCHES.md)** and the
**[comprehensive metadata CSV](ilvis0-current-findings-20261015/stretch-analytics.csv)**
preserve individual observations and outcomes.

**[What comes next](NEXT_STEPS.md)** covers focused recovery diagnostics,
measurement-contribution checks, predictions on unused observations and freely
estimating the background rotation rate. The [technical roadmap](ANALYSIS_ROADMAP.md)
retains the detailed development record.
