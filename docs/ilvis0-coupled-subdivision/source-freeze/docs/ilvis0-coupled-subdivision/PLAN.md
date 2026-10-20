# Smaller calibration boxes, with complete coverage

The completed broad-box comparison passes correctness but barely narrows the
ranges. Its saved remainder floors are below the target on all 18 known-feasible
axes. This study tests finer static-map bounds without recomputing native
trajectories or changing physical assumptions.

## Fixed partition and evidence

Reuse all 48 parents from the completed coupled-map prediction comparison.
Split normalized mounting coordinates 0 and 1 at their fixed binary midpoint.
The original eight yaw sectors remain unchanged. Skip fixed coordinates and
coordinates with no representable interior midpoint. Keep closed shared
boundaries. An independent exact construction must verify that all children
cover their entire parent without dropping any of the 27 physical coordinates.

Use the same rule for all six generated candidate/processing groups. Freeze
every child before evaluating its range; neither the known calibration nor
future truth selects a split. There are at most four children per parent,
**192 child identities total**. Cells are pieces of one uncertainty calculation,
not independent scientific observations.

Each child reconstructs the original source reference and keeps its radii,
native expression, all parent constraints and all 78 coordinates. Add necessary
complete-map relationships for the smaller physical box. Independently verify
their exported rows before contraction. Run at most eight contraction passes,
then six signed supports with the same independent endpoint audit as the parent.
No baseline support audit is rerun.

After the child's range or empty proof is saved, determine whether it contains
the sealed generated calibration. Check every containing child, including all
closed cells sharing a boundary. An empty containing child is a failure.
Never skip or replace failed, empty or unhelpful cells. The final six-group
range is the union of all surviving children and original yaw sectors.

## Finite allowance

At most 192 identities, partition audits, source setups, coupling audits,
eight-pass contractions and post-range truth audits; 384 interval-map evaluations;
1,152 one-second LP proposals and 4,608 exact support checks. Each signed proposal
reserves its two helper support evaluations plus one old-certificate reevaluation;
each endpoint audit reserves six more. Retain the 1,024-row/78-column contraction
cap. Four workers use one numerical thread each. Expected wall time is roughly
9–12 minutes; the cooperative ceiling is **960 seconds**. No retries, allowance
expansion, native predictions/bounds, original-aircraft reads or observed fits.

Every operation is durably reserved before execution. Charged interruptions
remain failures without replacements. Freeze sources, environment, parent inputs,
partitions, child identities and baseline targets before launch.

## Gate

All registered child calculations and cover audits must pass. Every generated
truth must remain in every containing child, and each group must have at least
one containing child. Compute outward union widths and compare the same fixed
twofold target on every axis with the original projected 7.2-second baseline.
Report the immediate parent comparison as well. Partial improvements do not
qualify observed predictions or full-flight uncertainty.

[Parent comparison](../ilvis0-coupled-prediction/INTERPRETATION.md) ·
[Saved range components](../ilvis0-coupled-prediction/DECOMPOSITION.md).
