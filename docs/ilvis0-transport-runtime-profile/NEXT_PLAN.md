# Accelerate conservative arithmetic before longer comparisons

The profiles are complete. Do not restart them. Preserve the six-source screen,
including both time-limit failures and all charged supports.

Implement a separate compiled backend for the measured hot paths: vector/matrix
radius arithmetic and small-matrix norm bounds. Keep every frozen implementation,
reference center, calibration domain, explicit reference row and 51-column native
expansion unchanged.

Each bound operation must round outward and include center-operation rounding
in its change and affine-error radii. Matrix norms may use outward trace and
absolute Gram-row sums, retaining the sharper valid bound. Guard IEEE binary64,
rounding mode and subnormal handling; disable unsafe contraction and fast-math.
Reject unsupported results explicitly rather than silently clipping them.

Validate primitives independently against exact rational calculations, including
zero, cancellation, signed entries, small magnitudes and near-overflow cases.
Retain both norm and coordinate bounds. Numerical comparison tolerances do not
establish mathematical enclosure; source-coefficient and whole-program rounding
qualification remain distinct.

Then freeze the original native control matrix under unchanged center,
derivative and containment limits. Only after it passes should a new long-history
screen run. Every study needs finite charges and must preserve failures.

Continue [source integration](../ilvis0-source-stream-controls/NEXT_PLAN.md),
including point-domain and clock-boundary checks. Whole-history performance,
complete width qualification and observed aircraft validation remain open.
