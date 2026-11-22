# Try to exclude high forecast scores using the linked physical calibration

Retain the whole saved cover of ESA development flight 187 and all eleven
surviving boxes. Use the first available reconstructed proposal in each box
from the checked witness study. Rebuild its linked physical coefficients
and use its normalized earlier residual as a direction. Skip a box if the
prior study supplies no usable linked point. Preserve its previous bound.

For each available box test two score floors. One is half the nominal
globe–disc gap minus 0.1 score units. The other is the highest floor from
the original threshold study. For each floor propose nonnegative weights
from one scaled linear program. Those weights only guide a certificate.
The certificate uses the outward score and earlier-loss coefficient
intervals, and evaluates the 24 shared terms as functions of the same 27
physical parameters. Keep every archived affine row and the full allowed
box of the nine auxiliary terms. The earlier loss increase stays at 0.01,
with zero additional earlier error.

For a candidate scoring at least the floor and passing the earlier loss
test, the weighted sum of the two constraint slacks and the archived affine
slacks must be nonnegative. A strictly negative outward upper bound on that
sum excludes the floor. Check each whole box first. If needed, split the two
physical coordinates with the largest derivative-width products for that
weighted direction. Check coverage and require every closed child to pass
before reducing the parent bound. A failed exclusion leaves the previous
bound in force. Verify that no certificate excludes a previously saved
linked witness in its domain.

Use two one-thread workers, with a 180-second cooperative limit, two LP
proposals and up to ten linked-support bounds at each available box. Save
all exclusions, exact arithmetic and coverage evidence. No new fit,
integration, later observation or reserved flight enters. This bounds the
saved linked surrogate, with its original numerical allowance. An
integration-error bound and aircraft error qualification remain separate.
