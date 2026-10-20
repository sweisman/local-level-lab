# Check whether the saved matrix examples represent rotations

The exact feasible-witness diagnostic shows that more linear optimization cannot
remove the failing widths. Before another propagation revision, test whether the
saved extreme examples preserve a known property of the physical force matrix.

That matrix is M = R_initial R(p) diag(1/(1+g)). Remove the proposed gains to
obtain B = M diag(1+g). A true rotation preserves the Gram spectrum: for an
exactly orthogonal initial matrix, BᵀB = I. More generally,
||BᵀB-I||_F² = ||R_initialᵀR_initial-I||_F².
The latter equality avoids treating a supplied floating initial matrix as exactly
orthogonal. Reconstruct M from all saved physical and matrix-error coordinates
using rational arithmetic. Compare its Gram defect with that of the original
initial matrix.

Local known-answer tests must cover identity, signed/permuted rotations, gain
removal, nonorthogonal initial matrices, stretched columns, equal-length but
nonorthogonal columns and malformed/nonpositive gains. Distinguish the exact
defect from an explicit 1e-8 dimensionless diagnostic allowance for the existing
floating matrix conventions. This is a numerical diagnostic threshold, not a
measured sensor specification or a replacement scientific gate.

After tests pass, freeze six identities from the completed width diagnostic.
Each examines its six saved exactly feasible witnesses and its physical anchor:
36 witness checks and six anchor checks, 42 matrix checks total. An incompatible
physical anchor fails qualification and blocks interpretation of that case.
Use the original saved generated configurations and source-bound matrix
references; verify all input hashes and complete 51-coordinate ordering.
Record reconstructed matrices, gains, exact Gram defects, reference defects,
allowance and every flagged example. Preserve near-threshold outcomes without
replacement or tuning. Four workers use one thread each, with a 60-second
cooperative allowance. No LP proposals, native calls/bounds, original aircraft
reads, observed fits or protected outcomes. No retries or budget expansion.

A flagged example diagnoses a nonphysical combination admitted by this
relaxation. It does not prove all permitted examples are nonphysical, justify
discarding the region or establish a narrower valid interval. A clean Gram check
is necessary, not sufficient: it does not establish the correct dependence on
the proposed orientation, full trajectory feasibility or aircraft uncertainty.
Any stronger future constraints need their own derivation and qualification.
