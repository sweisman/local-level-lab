# Bound orientation change separately for each column

The completed orientation-domain comparison passes correctness but improves
complete ranges by less than 0.2%. Preserve its failed usefulness gate, fixed
allowance and evidence. Do not repeat it or tighten physical calibration limits.

For y_j(v)=exp(skew(v))e_j, compare two rotation vectors with difference h.
Duhamel's derivative formula gives
||D exp(skew(v))[skew(h)] e_j|| <= ||h_perp|| + |h_j| ||v_perp||/2,
where perpendicular components omit coordinate j. Indeed,
||e_j cross exp(s skew(v))e_j|| <= s ||v_perp||; integrating the derivative
formula over s gives the factor one-half. Integrate along the straight path
between the expansion center and a permitted rotation vector.

Over the original physical box, define delta_k as the largest displacement from
the center in coordinate k, and m_k as the largest absolute coordinate value.
A valid column-distance bound is
D_j = min(2, ||delta||, ||delta_perp|| + delta_j ||m_perp||/2).
Use exact rational coordinate bounds and outward square roots. This cannot
exceed the previous common distance bound and correctly vanishes for a column
with only rotation about its own axis. The entire original orientation box
remains represented; this is not a narrower calibration assumption.

Substitute D_j into the already qualified directional support derivation.
Preserve the signed chord/tangent rule, degree-40 center polynomial and tail,
explicit center relaxation and outward coefficient exports. Keep all 51
coordinates, existing constraints and valid certificates. Frozen predecessor
sources must remain unchanged; implement this as a separate component.

Local tests must cover pure axial rotations, zero/point domains, mixed-axis
Rodrigues pairs, source rejection and the inequality D_j <= previous bound.
Check physical retention and a column case where the new bound is strictly
tighter. The derivative bound must be justified independently of the support
implementation, not inferred from a finite sample of passing probes.

Then freeze 24 controls: six preserved generated configurations crossed with
full, sector, point and gain-boundary domains, 64 independent physical probes
each. Allow 1,536 probes and 119,808 new support checks; report reused oracle
checks separately. Four workers use one thread each for at most 180 cooperative
seconds. Zero native integration or bounds.

Only after qualification passes, freeze all 48 saved sectors for comparison.
Allow 288 LP proposals, 1,152 exact support evaluations and 300 cooperative
seconds with four one-thread workers. Check known truth only after saving
predictions and independently audit every endpoint. Preserve the unchanged
twofold target and any remaining failures. No original aircraft reads, observed
fits, protected outcomes, retries or expansion of completed allowances.
