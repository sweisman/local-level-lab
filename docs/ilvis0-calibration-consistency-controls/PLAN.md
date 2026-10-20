# Calibration consistency qualification

Qualify six necessary inequalities tying the existing acceleration-remainder
and force-matrix-remainder coordinates to one physical calibration. Preserve
the 27 physical parameters, all 24 error coordinates and their original bounds.
These constraints add no observations or empirical calibration assumptions.

The derivation uses A = M(f-b) + g e_D. Preserve exact centre and derivative
mismatches. Bound the remaining matrix-change/bias-change product over the
whole box. A degree-40 rational exponential polynomial plus a geometric
factorial-tail bound certifies the reference rotation used in the change bound.
Export each row with a full-box outward allowance. An additional absolute
centre-mismatch relaxation preserves the existing point-domain zero-error
convention. It is explicit and cannot sharpen the continuous identity.

Freeze 24 identities: six preserved generated configurations, each under full,
sector, point and gain-boundary domains. Each identity permits 64 probes,
384 exact rational inequality checks and 192 matrix-column checks: 1,536
probes, 9,216 inequalities and 4,608 column checks in total. Use independent
Rodrigues and calibrated-force oracles. Include corners and single-coordinate
extremes. Known calibrations must satisfy every exported inequality exactly;
the independent oracle comparison has a separately reported numerical tolerance.
Point domains retain the declared zero-error convention. Synthetic large gains
stress the mathematics and do not change aircraft bounds.

Four workers use one thread each. Allow 120 cooperative seconds, with no retries
or extensions. Zero native calls, native bounds, original aircraft reads,
observed fits or protected ESA outcomes. Retain any failure under this freeze.
Standalone adapter loading and exact-affine local controls precede launch.

Passing qualifies these necessary constraints and their export, not full native
floating-point enclosure or aircraft uncertainty. A separate finite saved-case
comparison is required before claiming narrower prediction ranges.
