# Background-subtracted descriptive gyro plot

Preserve the original raw plot and all 53 selections. Add a companion using the
same recorded aircraft-right-axis gyro bins on the existing uniquely matched
receiver support. Omit unsupported edge seconds explicitly; do not interpolate
or invent corrections. Preserve gaps and both signs.

Subtract only the conventional specified background field projected onto a
declared level aircraft axis with heading equal to receiver-derived globe course.
Its positive nose-down contribution is Omega cos(latitude) sin(course), with
Omega fixed at 7.2921150e-5 rad/s. This is not a fitted or independently measured
field. Assume no upstream removal for this display. Keep globe transport,
aircraft motion, bias and other errors in the remainder. Do not subtract the
whole globe prediction or fused navigation rates.

Reuse hash-verified companion results and saved receiver selection. Check each
new raw sum and field sum against its already published matched-support summaries:
the field sum must equal specified-field globe minus zero-field globe. Plot all
53 curves and their median; distinguish the common interval from the changing
subset. Nose-down remains positive and increases downward. Do not flip curves
or tune a rate to make them agree. Publish raw, subtracted and remaining angles.

Finite plotting scope: 53 stretches, at most 1,000 matched bins and 1,500 receiver
fixes per stretch, 53,000 projections total, one worker/four numerical threads,
180 cooperative seconds. No source decoding, native integration, optimizer starts,
new model decision or statistical claim. Ordinary local tests cover independent
cardinal directions, sign, duration weighting, retained transport, ignored fused
channels and unfilled gaps. Provenance records source/output hashes and support
differences. This is a visualization, not a new Earth-model study.
