# Measured differences between the three GPS receivers preserve the shape preference

The fixed shape score for the AIR1 carrier path on ESA flight 187 was
**−7.13**. Negative values favor the zero-field globe over the zero-field
disc. Zero marks a tie. Applying the measured differences from two other
receivers on the same aircraft gave estimated scores of **−7.07** and **−7.28**.

| Raw carrier comparison | Later path correction, 3D RMS | Change in score | Estimated score |
| --- | ---: | ---: | ---: |
| Septentrio relative to AIR1 | 0.370 m | +0.062 | −7.070 |
| NovAtel relative to AIR1 | 0.339 m | −0.148 | −7.280 |
| NovAtel relative to Septentrio | 0.033 m | −0.210 | Relative shift only |

The calculation projected the measured range differences into position
corrections on the same satellites. It used 518 one-second intervals with
at least ten satellites each. Using the geometry at the opening or closing
half-second step changed the score shifts by at most 0.000024 units. The
one interval crossing the AIR1 receiver clock step was left uncorrected.
Within the linearized calculation, a one-metre unmeasured displacement at
that interval could change the score by at most 0.0028 units.

The comparison used the same earlier anchor and fixed shape forecasts.
It measures how much the observed differences between receivers affect
that comparison. All three share an antenna, so errors common to the
three solutions and the full calibration range remain open. No receiver
trajectory or inertial model was refitted. All 519 interval checks and
eight focused tests passed.

The same two alternate receiver excerpts also contain dual-band Galileo
observations at the comparison times. A format and tracking screen found
nine common satellites on 489 intervals and eight on the other 30. This
supports a separate-constellation replay if the Galileo navigation, timing
and phase-continuity checks pass.

[Frozen plan](ESA_RAW_RECEIVER_SCORE_PLAN.md) ·
[Numerical results](esa-raw-receiver-score-result.json) ·
[Execution receipts](esa-raw-receiver-score-evidence/README.md) ·
[Reproduction bundle](esa-raw-receiver-score-evidence/bundle.zip)
