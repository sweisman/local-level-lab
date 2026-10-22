# Bound the residual correction, including clock boundaries

The saved-point correction is now a useful approximation lead. The next work
must produce a valid enclosure rather than add another sampled-agreement claim.

Along a declared calibration path, let h(s) be the derivative of the remaining
error after the exact shared-source expression has been removed. Its integral
gives the error change. The endpoint average approximates that integral.

First qualify a small mathematical component for piecewise smooth h. Its
supplied bounds must include the second derivative of h within each segment,
plus jumps in h and its first derivative at every declared interior boundary.
Missing jump information must fail, rather than silently mean zero. Check
smooth affine/quadratic examples and independent step/hinge examples exactly.
Use rational arithmetic and outward endpoints.

The trapezoid-error kernel is K(s)=s(1−s)/2. A conservative error allowance is
the sum of each smooth bound times the integral of K on its segment, each
slope-jump bound times K at the boundary, and each value-jump bound times
|K′| there. The component must explicitly distinguish supplied mathematical
assumptions from verified native-clock coverage.

Then identify how the native calculation can supply those bounds over the
complete declared calibration region and clock support. Reuse qualified source
derivatives, but do not assume that their bounds automatically cover native
trajectory derivatives. Packet-boundary counters alone do not establish
smoothness. Reference arithmetic and any discontinuity in the residual itself
also need an explicit treatment.

Only a separately qualified native enclosure, retaining every calibration
region and the full prediction period, can advance V01. A mathematical
component or good results at the twelve known points cannot do that alone.
No new native or observed-fit allowance is implied by this plan. Any such
study requires its own tested finite source/input/environment freeze.
