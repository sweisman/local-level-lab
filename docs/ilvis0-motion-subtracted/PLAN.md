# Navigation-assisted gyro visualization

Add a third display after the raw and background-subtracted plots. Preserve all
53 selected intervals and existing research results. Reuse the second plot's
hash-checked receiver/gyro timestamp support and the preserved descriptive cache.
No new originals are decoded and no model is fitted.

The cache subtracts aircraft angular motion calculated from Group-1 roll, pitch
and heading changes, rotates the remaining raw gyro vector into local navigation
axes, and projects it across the ground track. Its across-left sign is the
nose-down tilt sign for a level aircraft aligned with its course. This axis is
different from the fixed aircraft-right axis in the first two plots. Preserve
that distinction in labels and exported values. Fused gyro-rate channels do not
enter this calculation.

Subtract the specified full-retained background field from that cached rate:
Omega cos(latitude) sin(course), with Omega=7.2921150e-5 rad/s. Use the spherical
receiver course convention of the cache, associated with the same receiver
interval as the second plot. The cached correction originally associates
attitude/course with each raw bin's actual center; the display uses its preserved
UTC-second receiver match. This coarse association is a visualization assumption,
not a precision motion correction. No transport prediction is subtracted.

Require a valid cached motion correction on every matched second before plotting
a complete stretch. Inventory all 53 outcomes. The expected 52 supported traces
are drawn; the one unsupported stretch remains listed, never filled with zeros,
substituted raw gyro values or interpolated corrections. Preserve signs and gaps.
Keep degree/minute units and downward-positive tilt. Use the raw plot's vertical
range unless that would clip a new trace; record any necessary expansion. Show
the common-cohort median and a separately labeled shrinking-cohort median.

Finite rendering scope: 53 stretches, at most 1000 bins and 1500 receiver fixes
per stretch, 180 cooperative seconds, one numerical thread with two reserved
for the active long-record study. Scratch/cache files stay in the project data
directory. Save the plotted bins, all-stretch outcomes, source/input/output
hashes and support counts. Fail on changed inputs, invalid values or inconsistent
cache/raw support. Ordinary local tests verify signs, duration weighting,
retained transport, omitted support, gaps and forbidden fused-rate substitution.

This is a navigation-assisted illustration. Group-1 attitude shares the IMU and
navigation model. The remainder includes transport and measurement/correction
errors; it is not isolated curvature or independent evidence. Keep it outside
research observations, model comparisons, thresholds and scientific decisions.
