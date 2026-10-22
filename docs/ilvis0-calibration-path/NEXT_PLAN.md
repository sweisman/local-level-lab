# Supply complete native curvature bounds

Two mathematical inputs now exist: the piecewise quadrature-error allowance,
and calibrated/partial-packet derivatives through third order. They do not yet
provide the native quantities required by the first.

The separate [third-order derivative algebra](../ilvis0-path-jets/README.md)
now passes independent product, reciprocal and rotation checks, with actual
derivatives distinguished from factorial coefficients. Connect it to the
native packet-to-position adapter next. The [motion-step expressions](../ilvis0-path-motion/README.md)
also pass focused checks. Reuse the exact packet derivatives;
do not edit frozen native engines or restart their studies.

Propagate derivative bounds through the actual rotation, midpoint velocity,
position and receiver-coordinate equations. Work with the residual after the
shared-source expression so known calibration nonlinearity is not bounded
twice. Do not subtract two unrelated enormous ranges and call that a useful
residual enclosure.

Clock treatment must identify every supported packet branch over the declared
domain, verify its completeness, and bound one-sided derivative jumps. Keep
ideal packet-time geometry, native cumulative floating-point timestamps and
numerical execution error distinct. The quadrature component assumes a continuous
residual; any discontinuity or numerical deviation needs an explicit allowance,
not a missing jump entry.

Before full-history work, freeze finite controls for smooth known motion and
clock-boundary crossings under all candidate/processing cases. Record measured
costs, useful-width requirements and every charged evaluation. A complete native
enclosure must then cover the intended history/prediction period and physical
domain. The aircraft error law remains a separate requirement.

This plan supplies no new native or observed-fit allowance by itself. Every
new numerical study needs a separately tested finite source/input/environment
freeze. Completed studies, failed labels and original measurements remain intact.
