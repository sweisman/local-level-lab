# A small orientation change can hide the north–south force signal

For the constructed error that spans the ESA shape-score gap, the two
predicted force directions can coincide with **at most 0.181 mrad**
(0.0104°) of rotation on each tested support. The rotation axes were
within 1.17° of horizontal, so almost all of the adjustment is tilt.
The force-magnitude difference that survives that rotation reaches
**0.0231 mm/s²**.

| Averaging support | Model | Rotation needed, range | Largest change in force magnitude |
| --- | --- | ---: | ---: |
| 10 s | Zero-field globe | 0.003–0.181 mrad | 0.0099 mm/s² |
| 10 s | Zero-field disc | 0.003–0.180 mrad | 0.0098 mm/s² |
| 24 s | Zero-field globe | 0.029–0.126 mrad | 0.0231 mm/s² |
| 24 s | Zero-field disc | 0.029–0.126 mrad | 0.0229 mm/s² |

An earlier GIRAFE campaign estimated platform alignment error at up to
1.5 mrad. That provides a scale comparison for the angles here. The
alignment on this flight remains unmeasured at the required scale.
[Earlier campaign, Appendix A4](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022JB025921)

These are individual force averages. Each pair can use a different
orientation, so the calculation leaves the platform's actual tilt and
its time dependence open. Agreement of the two [vertical file exports](ESA_GIRAFE_LEVEL1_AIRBORNE_RESULT.md)
cannot constrain that tilt. The shape comparison receives no new decision
from this check.

Ten support evaluations reproduced the sealed horizontal magnitudes.
Seven software tests passed. The run used no new sensor reads, model fits
or reserved-flight reads.
[Frozen plan](ESA_GIRAFE_TILT_IDENTIFIABILITY_PLAN.md) ·
[All predicted vectors, angles and charges](esa-girafe-tilt-identifiability-result.json)
