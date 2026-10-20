# Training-derived acceleration bounds

Test whether the complete training constraints bound reference acceleration more
tightly than its individual calibration coordinates suggest. This uses saved
generated controls; it does not integrate or fit aircraft observations.

Keep the original 51-coordinate training region, its contracted box, physical
limits and source-bound acceleration expansion. For each of its three components,
bound the full affine expression in both directions. Use nonnegative LP-proposed
dual certificates, exact rational support arithmetic, and an independent exact
verifier. The constant shift includes the unchanged physical expansion center.
Columns 39–41 carry the acceleration remainder; columns 33–38 do not replace it.

Select the unique previously declared known-truth sector in each of the six
model/processing groups from the completed column-orientation comparison. This
is a development control, not selection of an aircraft interval. The bounds receive
only training constraints and saved reference metadata. Save their coefficients,
certificates and endpoints before opening a separate known-anchor input. Use that
anchor only to check feasibility and containment afterward.

Finite allowance: six identities, six signed LP proposals per identity, one second
per proposal, and three exact support evaluations reserved before each proposal.
The two checks inside the proposer and independent verification therefore total
at most 36 LP proposals / 108 exact support evaluations. Do not repeat source
future-certificate audits in the task. Preparation verifies sealed prerequisite
receipts. Four workers use one numerical thread each, with a 180-second cooperative
wall allowance. Zero native evaluations, integration bounds, original-file reads,
observed fits, retries or budget expansion. Charge before execution, including
failed or interrupted proposals.

Local tests must cover correlated coordinates, signed objectives, shifts, zero
caps, source/parent mismatch, full column mapping, absent future observations,
independent certificate disagreement, counters and save-before-anchor ordering.

Usefulness requires at least a twofold reduction in the Euclidean acceleration
change radius in every group, using outward endpoints and an exactly checked
upper square root. Report all six outcomes, including failures. This engineering
criterion does not replace the prediction study's unchanged twofold width target.
Even success requires a separate qualified propagation candidate before new
prediction ranges. Keep original reference and remainder allowances unless a
new bound independently justifies changing them. No observed fit is authorized.

Publication copies hashed results and sources without recalculation. Preserve
completed evidence and disclose computational failures without replacements.
