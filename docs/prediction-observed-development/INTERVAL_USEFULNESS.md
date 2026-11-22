# Can the generated range separate models?

The fixed changing-drift law produced a **25.59 m median half-width per
coordinate at the last withheld second** in its completed 256-history
generated check. That check failed its preset coverage gate, so this is
an exploratory width, not an accepted aircraft uncertainty range.

For two predictions at one time in one coordinate, ranges with centers
`μ₁`, `μ₂` and half-widths `h₁`, `h₂` are disjoint only when
`|μ₁ − μ₂| > h₁ + h₂`. If each has a 25.59 m half-width, their centers
must differ by more than **51.18 m** for those two endpoint ranges to be
disjoint. Overlap of one-coordinate ranges does not rule out a decision
using an entire time-correlated trajectory; that requires its own joint
contrast calculation and calibrated decision rule.

A later [matched 24-fit ESA development check](ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)
now supplies three-model forecasts on the same 400-training/120-future cut.
In its two complete profiled-removal settings, the raw future horizontal RMS
is about 5.18 m for the specified-field globe, 2.59 km for the zero-field
globe and 4.00 km for the tested disc. The zero-removal settings remain
unresolved after flat-model stopping failures. The earlier 0.56 m
single-model figure used a separate training-only forecast correction;
it is not the raw matched score quoted here. No generated range has yet
been justified as an aircraft confidence interval, so these matched errors
do **not** establish calibrated separation or an independent detection.
Reserved ESA flight groups stay closed.

## Check against already saved model forecasts

An earlier [ESA height-dependent-gravity pilot](../esa-observed-height-pilot/README.md)
has one complete three-candidate comparison. Its three training-selected
forecasts use the same 800 earlier receiver positions and the same 400 later
times. Using the repository's common `receiver_errors` coordinate conversion,
the forecast centers differ by the following distances. These are distances
*between model predictions*, not their errors against the receiver:

| Forecast pair | At 60 s | At 120 s | At 400 s |
|---|---:|---:|---:|
| Globe with specified field / globe with zero field | 673 m | 1,281 m | 8,039 m |
| Globe with specified field / tested disc | 1,423 m | 2,659 m | 15,507 m |
| Globe with zero field / tested disc | 770 m | 1,404 m | 7,520 m |

The source forecasts are the `sphere_rotating`, `sphere_still` and `flat_still`
`-0-reported-persistent-v1-0/forecast.json` artifacts in the verified
`data/esa-observed-height-pilot-20261023` study. Their archived SHA-256
prefixes are `5c860c4f`, `6666e107` and `4bd13f63`, respectively. The
calculation aligns all 400 later timestamps, converts each pair's latitude,
longitude and height differences to local north/east/up metres using
`lll.airquantumgrav_scoring.receiver_errors`, then takes the Euclidean norm
at later epochs 60, 120 and 400. The 60-second comparison matches the
duration of the generated range check, although the aircraft's error law
has not been established.

This check establishes that **forecast-center separation is large on that
one development interval**. It does not transfer the 25.59 m generated
half-width to an aircraft, certify the zero-field or disc fit as physically
adequate, establish coverage, or decide between models. The earlier pilot
qualified only one of four full matched settings. A new matched three-model
forecast under a *qualified* aircraft error law remains the decision gate.

The separate [fresh generated check](threshold-42-validation/RESULT.md)
qualified a wider **4.2** threshold for its specified simulator: 1/128
whole-history failures without the generator's vibration and 0/128 with it.
Its median endpoint half-width was **29.57 m** per coordinate. Two such
one-coordinate endpoint ranges would need centers more than **59.14 m**
apart to be disjoint. This still cannot be applied as an aircraft confidence
range until the actual flight's changing errors and calibration uncertainty
are justified.
