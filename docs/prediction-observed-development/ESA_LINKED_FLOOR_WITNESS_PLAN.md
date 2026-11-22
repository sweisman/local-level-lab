# Check whether the relaxed calibration model admits a high shape score

Use all eleven surviving calibration boxes from the sealed score-floor study
on ESA development flight 187. For each box take the highest threshold that
the prior study tested. Preserve its position loss allowance of 0.01, zero
additional earlier error and all 60 coordinates. Two saved disc proposals
above the 25.41-unit forecast gap had residual norms inside the earlier
radius. The proposal records alone did not prove that the coupled affine
constraints and earlier loss could hold together.

Use the archived residual direction and norm for each box to propose a
solution by linear programming. Compress the earlier design by QR. Within
the original static constraints, seek the closest attainable compressed
residual to the saved proposal in maximum-component distance. Try two
predeclared versions, with zero inward margin and a relative inward margin
of 1e-9 on movable bounds and rows. The stronger constraints only guide
the search. Check each point in the original box and all archived affine
rows by exact binary rational arithmetic. Check its earlier loss and score
with the archived outward evaluator. Preserve constraint violations and
missed thresholds. A certified point in this relaxed model does not establish
that its independent calibration coefficients are physically attainable.

For each proposed point also recompute the shared terms from its first 27
coordinates as one physical calibration, and evaluate the same earlier loss
and signed forecast contrast with the saved surrogate. Record whether the
point keeps its high score after imposing that physical link. This is a
surrogate check. It does not integrate a new physical trajectory or establish
legitimate bounds on the nonlinear residual.

Eleven tasks run on two one-thread workers, with a 120-second cooperative
limit, at most two LP proposals and four outward point checks per box.
No new inertial fit, native integration, withheld receiver observation or
reserved flight enters the calculation. Keep the prior results unchanged.
