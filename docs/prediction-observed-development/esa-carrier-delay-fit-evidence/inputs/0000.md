# Estimate a shared atmospheric delay from the earlier GPS carrier data

Use the sealed continuous GPS carrier path and its satellite deletion
diagnostic from ESA development flight 187. Use the same satellites,
positions, clock step, elevation mask and two-minute withheld interval.
No new inertial fits or protected flight reads.

1. Implement and test a linearized carrier calculation in
   `lll.esa_carrier_delay_fit`. Give each endpoint a zenith-delay discrepancy
   of `offset + slope * elapsed_s / 400`. Map it to a satellite range with
   the existing plane-parallel elevation factor. Difference the two ends of
   each half-second step. Remove the four fitted position and clock directions
   at that step. Propagate the accumulated position perturbation through
   both range Jacobians before proceeding to the next step.
2. Recover the unprojected geometry using the exact archived receiver and
   satellite inputs. Reconstruct the orthogonal residual using the archived
   leave-one-satellite-out errors and the endpoint leverage. Require both
   the residual RMS and displacement gains to reproduce.
3. Fit the two coefficients using steps between the 400 earlier reports.
   Require full numerical rank and report both singular values, the fit
   coefficients, and the residual change on the 240 later half-second steps.
   Fit no coefficients using the later interval. Report the induced later
   position shift, fixed shape score and all four original position limits
   for both existing preferred forecasts. Check the original GPS carrier
   scores before interpreting the new path.
4. Test the propagation on a generated known-answer case with varying
   geometry, adverse later errors and one degenerate design. Freeze one
   task with one thread, a 120-second cooperative cap, 1,038 charged
   geometry steps and no inertial calls. Preserve the study and report.

This is a two-term atmospheric sensitivity check. Its range residuals
can contain other errors, including satellite or receiver effects. The
linearized fit has no calibrated coverage and does not bound arbitrary
errors shared by all receivers. The position sensitivity uses the first
receiver position as its fixed anchor.
