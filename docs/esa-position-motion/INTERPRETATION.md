# Position-based motion software passes its first qualification

All ten identities passed: 24 analytic paths and 2,304 noisy realizations.
The supplied-error calculations covered all nine trend coefficients in 252–256
of 256 realizations per family. Their exact one-sided 99% coverage lower bounds
are at least 0.955, above the frozen 0.95 requirement. The arbitrary-correlation
bound covered every realization.

Ignoring correlation is materially different. In correlated families, the
independence calculation covered only 103–127 of 256 realizations. A smoother
position-derived path therefore cannot justify treating its errors as independent.
At the largest simulated noise, point estimates also produced false turn flags.

The analytic paths check the changing geographic metric, both hemispheres,
longitude wrapping, nonuniform epochs, turning and climb. Maximum course error
was 1.81e-10°/s and maximum speed error 8.22e-10 m/s. These are software agreement
figures, not real receiver accuracy.

The run took 18.5 seconds and reconciled all 2,328 reserved assessments. Every
generated input and interval is retained. No receiver file, gyroscope observation
or protected confirmation group was read. The existing ESA selection still admits
zero intervals.

Next is a separate, bounded receiver-only comparison on development recording
187. It will retain unsupported windows and distinguish uncertainty in a fitted
trend from unknown instantaneous aircraft motion. The real receiver covariance
and its temporal behavior remain uncalibrated.

[Results](README.md) · [Frozen scope](PLAN.md) · [Next assessment](NEXT_PLAN.md).
