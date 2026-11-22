# Test high forecast scores against the full earlier loss constraint

The [joint score check](ESA_LINKED_JOINT_SCORE_RESULT.md) found only a small
improvement from additional linear approximations to the original loss ball.
Its highest-scoring disc proposals still exceeded the earlier residual
radius by hundreds of whitened units. Keep the same eleven contracted
calibration ranges, all 60 coordinates, the archived score, zero earlier
unshared error and the original 0.01 squared-loss allowance.

For each range, test four score floors. Start the search between zero or the
highest saved feasible score, whichever is greater, and the previous checked
upper bound. Test the midpoint. An exact proof that the floor is impossible
moves the upper endpoint down to that floor. Otherwise, move the lower search
endpoint up. A failed proof supplies no feasible point or scientific lower
bound. Preserve all earlier dispositions and the complete cover.

At each floor, enclose the signed forecast score with the same checked
coefficient allowance. Add the necessary affine inequality for reaching the
floor to every saved static and training row. First seek a verified affine
infeasibility certificate. If needed, minimize the full earlier squared
residual on that high-score region. Use the residual at the proposed point
to construct one necessary training inequality with the existing outward
calculator. Prove that its upper limit is below the smallest possible left
side in the high-score region using nonnegative dual weights and two exact
evaluators. A solver status cannot exclude a score by itself. Every previously
verified feasible score must remain consistent with the final bound.

Freeze eleven tasks on two one-thread workers and a 180-second cooperative
limit. Each task can test up to four floors, with one affine proposal and one
minimization proposal capped at 120 iterations per floor. Charge the exact
checks in advance. Report all tested floors and the combined bound. No model
fit, new measurement, later receiver position or reserved flight enters this
static calculation. The integration remainder and observed error law remain
open even if the static bound improves.
