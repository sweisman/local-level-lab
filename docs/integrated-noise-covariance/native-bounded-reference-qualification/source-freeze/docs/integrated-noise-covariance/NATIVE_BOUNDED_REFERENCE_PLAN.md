# Qualify the corrected dense reference

The [exact-arithmetic diagnosis](native-bounded-numerics/README.md) shows that the
original dense test used a general LU solve on an ill-scaled triangular factor.
Rational forward substitution supports the structured calculation and a proper
triangular solve. The former 22/24 outcome remains fixed and unqualified.

Change only the dense reference's two whitening solves to triangular solves.
Keep the same physical candidates, generated inputs, coefficient bounds, all
26/27 columns, zero linear-control remainder, error allocation, rank cutoff and
endpoint agreement tolerance. No production forecast or calibration fit changes.

Freeze a fresh full 24-case qualification with the same finite limits: one
numerical thread, two libraries, a three-minute cooperative allowance, 450 native
calls / 15,000 packet steps / 300,000 packet-query visits per case. Totals are
10,800 calls, 360,000 steps and 7,200,000 visits. There are no optimizer starts,
noise draws or original/protected reads. Unused charges stay charged.

Passing will qualify this native interface for the stated **linear** problem.
Missing nonlinear remainder allowances must still abstain. The result will not
qualify nonlinear coverage or release additional observed fitting.
