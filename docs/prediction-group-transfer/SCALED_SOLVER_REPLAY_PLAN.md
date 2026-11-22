# Parameter scaling on saved generated flight derivatives

Use the final saved training derivatives from the zero-start trust-region
fits in the six 120-second generated histories and the completed 24-second
generated baseline. Verify the parent manifests, fit artifacts and all 26
normalized calibration columns. Form an exact linear problem from each
saved derivative `J`, with observation differences `J*(x - target)` and
three extra residual rows `[102, 0, 0]` that are constant. The target is the
saved parameter vector with coordinates of magnitude at least 0.99 snapped
to their corresponding box limits. It is feasible and attains the known
minimum. Start both methods at zero and use the exact original box.

Compare centered L-BFGS-B with and without a fixed diagonal change of
coordinates given by the starting Jacobian's column norms. Use a small
positive floor only for nearly zero columns and transform the box and
gradient with the same scale. Keep every column. Run at most 14 starts,
200 residual evaluations each, one thread and a 90-second wall limit.

Report column and singular-value ratios before and after scaling. Require
an unchanged fresh numerical check and maximum absolute training difference
from the target at most 0.0001 whitened units. Report maximum parameter
error and solver flags separately. The check treats whitened residuals as
synthetic observation coordinates to exercise the stopping code. It does
not test position accuracy in metres, native propagation, nonlinear solver
convergence or predictive coverage. Use no aircraft recordings or new
native evaluations.
