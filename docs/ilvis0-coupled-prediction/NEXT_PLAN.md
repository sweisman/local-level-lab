# Test smaller physical calibration boxes

The complete map is correct on its declared controls, but broad derivative
enclosures barely narrow prediction ranges. Saved remainder floors are below
the target on all 18 known-feasible axes. Test finer physical boxes before
recomputing native trajectories or remainder bounds.

For every original orientation sector, split normalized mounting coordinates
0 and 1 at their fixed midpoint. The yaw coordinate already has eight sectors.
This gives at most four children per parent and **192 child identities** in
the complete six-group comparison. Skip unsplittable fixed coordinates, preserve
shared boundaries and prove the child boxes cover the entire parent. Use the
same rule for every group, without opening generated truth to choose a split.

Each child retains the original reference, normalization radii, all parent
constraints, native expression and unshared allowances. Recompute only the
static-map relationships on its smaller physical domain, contract and audit
its six future supports. Union all surviving children and original yaw sectors;
do not report only the favorable cells. Check known truth after bounds are fixed,
including all containing children when it lies on a shared boundary.

Before launch, qualify partition coverage and the new adapter. Freeze at most
192 setups, 384 interval maps, 192 coupling audits, 192 eight-pass contractions,
1,152 one-second LP proposals, 4,608 exact support checks and 192 truth audits.
Keep all 78 coordinates and the 1,024-row cap. Four workers use one thread each;
the proposed cooperative allowance is 960 seconds. Based on the completed
parent run, expected wall time is roughly 9–12 minutes. No retries, native
predictions/bounds, original-aircraft reads or observed fits.

All child correctness checks and the unchanged original twofold width target
must pass in every axis/group. Partial success cannot qualify observed work.
If this remains too loose, use the saved row/range diagnostics to choose the
next method; do not expand this allowance or silently increase the tree.
