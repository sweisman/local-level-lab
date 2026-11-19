# Two solvers agree on a new ESA flight window

Both solvers converged in all **16 pairs**. The two ways of computing the
derivatives also agreed under the frozen comparison rule in **all eight
settings**. The widest separation between predictions from near-tied
starting points was **0.265 mm** across 400 later timestamps. The predefined
limit was 10 mm.

The study used a previously unused 20-minute window on ESA development
recording 187. Each pair fit the same 800 GPS positions and the same inertial
increments. The 16 pairs cover two globe models, two assumptions about
upstream field removal, two GPS error descriptions and two starting points.
The later GPS positions stayed withheld. Both solvers retained every fitted
parameter.

Four settings picked different starting points as their lowest-cost fit.
Each pair of same-start costs agreed within the relative tolerance of
`1e-8`. The two starting points were close enough in cost and predicted
position to count as equivalent under the rule frozen before this run.
The earlier studies keep their original outcomes under their own rules.

The benchmark establishes agreement on this window and these globe settings.
Prediction accuracy requires comparing the paths with later measured positions.
The wide and selective variants used 288 and 304 fit evaluations,
respectively. Whole-fit speed still needs a separate measurement. The
flat-disc calculation and other recordings require their own checks.

The run closed with 624 charged native calls and no errors. The report
verifies the completed manifest, the sealed fit results, and the
comparisons over the forecast timestamps. Manifest SHA-256
`9e4f8af256bab5270a216b5d83c97b614a69a1ede6270ec10574fa7caa3c4d1f`.
[Results for all pairs and settings](observed-dispatch-fresh-result.json)
