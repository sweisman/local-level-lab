# What makes the generated forecast ranges wide?

The [saved interval audit](GENERATED_BOUND_COMPONENTS_PLAN.md) verifies the
closed two-case generated pilot and separates each forecast range into a
calibration part and a future-noise part. No fit or aircraft-data read was
performed.

| Generated error law | North: calibration share | East: calibration share | Up: calibration share |
|---|---:|---:|---:|
| Increment | 72.6% | 71.3% | 81.2% |
| Point | 72.6% | 71.3% | 81.1% |

These are median shares of the **marginal interval half-width** over 300 later
epochs. The calculation uses all 26 retained calibration directions and the
pilot's assumed affine Gaussian error law. Calibration uncertainty supplies
most of the width in this calculation. It does not measure the actual
aircraft error law or explain why either fitted trajectory missed its known
generated path by more than 90 m. Both point fits still fail the physical
accuracy screen; the aircraft error law remains unqualified.

[Verified machine report](generated-bound-components-result.json) ·
[Original generated pilot](BOUND_AWARE_GENERATED_PILOT_V2_RESULT.md)
