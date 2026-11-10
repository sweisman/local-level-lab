# Receiver-only development assessment

This is a finite retrospective check of the first **292 receiver epochs** of
selected stretch `570b37d23af5e245dd461051`. The saved split specifies GPS
week seconds 132350 through 132641, inclusive. Only the primary receiver's
saved `gps-fixes.csv` supplies observations. The source SHA-256 is
`b37b704b907f7a276976ae6f347b0d92a85cca7dc4d53d7a1c301ec2827ad9c4`;
the saved split SHA-256 is
`6c6e99ac5fbd31da56aa4d610b70677065595429005156af1b6d0ebc9e21674e`.
The 292 selected rows have fix quality 1 and one-second spacing. A new input
artifact must contain only these rows; later receiver positions must not enter
the assessment API. No original IMU recording is read.

Use a fixed decimal coordinate chart, with north =
111000 × (latitude + 60) metres, east = 55500 × (longitude + 75) metres, and
up = ellipsoidal height − 12000 metres. This chart is a numerical reference,
not a competing Earth model or a curvature measurement. Its origin and scales
are fixed here before calculating residuals. Set training time to 0 at the
first row and 1 at the last, using exact rational intervals. Fit polynomial
reference coefficients of degrees 3, 5 and 7 from training rows only; round
each coefficient to twelve decimal places before the exact residual calculation.
Any coefficient vector gives a conservative upper scale bound under the fixed
reference-space and covariance assumptions, though a poor fit widens it.

Assess two fixed Gaussian covariance families. Both have independent white
standard deviations 0.3/0.3/0.7 chart metres for north/east/up. Each of the
OU, common-offset and end-of-training linear-drift components has standard
deviations 1/1/3 metres. The one-second OU transition is exactly
904837418036/10^12 for the nominal 10-second family, or
996672216055/10^12 for the nominal 300-second family. These are rationalized
research assumptions, not measured receiver-noise properties. Drift uses the
normalized 0-to-1 training time.

Calculate all **six** family/degree settings and all three axes, for 18 exact
quadratic assessments. Use one thread, a maximum of 18 charged assessments,
292 epochs per assessment, 32,768-bit rational numerator/denominator limit,
30 seconds per assessment and a 10-minute cooperative study ceiling. Set
alpha = 0.01, inverse-moment order 16 and a 10^-6 outward decimal grid. Preserve
every outcome and abstention. There are no retries, original-IMU reads, native
integrations, Earth-model fits or protected ESA evaluations. Freeze the prefix,
sources, environment, task list and limits before calculation; publish from
saved results without recalculation.

This can assess a **shared scale under each declared covariance law**. It cannot
establish that either law describes actual receiver errors, calibrate aircraft
prediction coverage or alter the 53-stretch model comparison. Do not choose a
family or polynomial degree using Earth-model rankings.

[Software qualification](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
