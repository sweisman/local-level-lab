# Qualification of shared vector-norm constraints

The existing source-bound constructions supply Euclidean caps for seven error
vectors: the initial lever remainder, three acceleration/clock vectors and the
three force-transform columns. Audit and qualify those actual derivations.
Equal component caps alone do not establish a norm bound. The three
velocity/clock coordinates remain componentwise and receive no unit-ball claim.

Retain all 51 coordinates and original physical bounds. For each verified
normalized three-vector, add 26 necessary inequalities using nonzero directions
in {-1,0,1}³ and outward square-root upper bounds. These form an outer polytope
of the Euclidean unit ball. Source-qualified zero caps use the existing
zero-error normalization convention and a zero right-hand side.

Freeze 24 identities: six preserved generated configurations under full,
sector, point and synthetic gain-boundary domains. Allow 64 physical probes
each, including corners and each coordinate's extremes: 1,536 probes,
10,752 independent vector-norm checks and 279,552 exact rational inequality
checks in total. An independent Rodrigues/force/lever-derivative oracle checks
the physical error vectors. Check all matrix-column indices and exclude the
unsupported velocity block. The large-gain control changes no aircraft limits.

Four workers use one thread each, after the current verification run releases
its allocation. Allow 180 cooperative seconds. Zero native integration calls,
native bounds, original aircraft reads, observed fits or protected outcomes.
No retries, extensions or process signals. Preserve any failure in this freeze.

Local tests check unit-ball support, rejection of the independent cube, source
and block provenance, zero caps and standalone adapter loading. Passing qualifies
only this mathematical relaxation; a separate saved-case comparison must assess
whether it narrows useful ranges. Whole-program floating-point enclosure and
aircraft measurement-error adequacy remain open.
