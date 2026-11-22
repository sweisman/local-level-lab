# Receiver motion in longer flight candidates

The fixed profile closed 29 preselected candidate tasks; 29 produced complete receiver-motion summaries and 0 did not. No Earth-model fit was run.

The [per-candidate table](motion.csv) reports recorded course change, climb, speed and measurement support. Thirty-second receiver-coordinate regressions reduce single-fix jitter; unsupported endpoints and gaps are not filled. The WGS84 metric is used only to describe motion in the receiver coordinate chart.

For context, 9 of 29 profiles have 95th-percentile absolute climb above 1.5 m/s, and 14 have 95th-percentile absolute course-change above 0.05 degree/s. These are reference values from the earlier fused-motion screen, **not acceptance decisions**. Receiver course is not aircraft heading; these summaries cannot establish roll or eliminate wind crab.

Next, freeze a receiver-motion selection and a full nuisance information check before using any new interval in Earth-model fitting. The original 53 selected stretches and reserved ESA groups remain unchanged.
