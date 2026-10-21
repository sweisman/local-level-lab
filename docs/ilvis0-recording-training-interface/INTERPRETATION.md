# Longer studies must state their own measurement allowances

**All 15 focused interface checks pass.** The new training-row builder requires
an explicit error allowance for every observation coordinate. It cannot silently
inherit the short example's 1 mm assumption. Supplying 1 mm explicitly reproduces
the old builder's rows exactly; the completed short studies remain unchanged.

Independent rational calculations check every constructed inequality and its
outward rounding. Increasing one allowance relaxes only its own two inequalities.
All 78 coordinates remain, including unidentifiable physical directions and
shared expression terms. No future observation enters this interface.

The interface constructs necessary constraints from supplied bound reports. Its
caller still has to verify those reports' provenance, full-domain validity and
the justification of the error allowances. It does not establish a noise law or
make the larger ranges useful by itself. The 49-test combined check also passes
the earlier direct-interface and accumulated-noise component tests.

[Scope](PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Recording-length requirements](../ilvis0-three-source-complete/NEXT_PLAN.md).
