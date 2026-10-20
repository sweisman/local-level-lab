# Joint rotation-product qualification

Qualify necessary relationships between force-matrix columns before using them
in a prediction comparison. Preserve every completed source and result.

The construction retains all original 51 coordinates and 27 physical parameters.
Nine additional coordinates represent matrix-entry/gain products; eighteen
represent squares and cross-products of the resulting rotation columns. These
are arithmetic relaxations, not additional physical calibration freedom. Use
four McCormick planes per product, a midpoint tangent for each square, and
joint Gram bounds. There are 78 coordinates and 129 new inequalities.

Bound the exact binary-input initial mounting matrix's Gram defect by its
Frobenius norm. Do not repair it to an exact identity. Add a separately declared
dimensionless 1e-8 numerical-control allowance; it is not an IMU specification
or a complete roundoff proof. Export coefficients and bounds outward over the
complete extended box. Gram constraints and relaxed product planes remain
necessary, not sufficient, for physical realizability or a proper rotation.

Local checks cover exact signed product corners/interiors, anisotropic gains,
zero-width domains and caps, source mismatch, invalid gains, nonorthogonal
initial matrices, joint-incompatible unit-length columns and reflected matrices.
The adapter tests prohibit rerunning the old physical oracle and reject a
changed source or extra probe. Twelve focused checks pass before this freeze.

Reuse exactly the 24 sealed column-orientation control identities: six generated
candidate/processing configurations crossed with full, sector, fixed and near-gain-
boundary domains. Reconstruct only the configuration-bound matrix component.
Require its binding to match the sealed source, then apply the new inequalities
to the existing 64 independently generated physical probes per identity. Do not
regenerate probes, change their values or call the old oracle again.

Freeze 24 identities / 1,536 reused probes / 3,096 plane constructions /
198,144 exact inequality checks / 119,808 coordinate-bound checks. Reserve each
identity's complete work before construction/checking. Four workers use one
numerical thread each, with 180 cooperative seconds. There are zero LP proposals,
native integrations or bounds, new physical-oracle calls, original-aircraft reads,
observed fits or retries. Interrupted work remains charged; no expanded allowance.

Require all original and extended coordinates to stay in bounds and every
exported inequality to retain every physical probe. Publish failures without
replacements. A passed component may enter a separately frozen complete saved-
prediction comparison; it does not establish narrower widths, calibrated
observational coverage or permission for observed fitting.
