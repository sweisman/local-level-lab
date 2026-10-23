# Checked local steps for training-compatible alternatives

Qualified first-step controls.

Usable steps were found in **12/12 directions**. Each direction tests three fixed step sizes, keeping the original 27 calibration coordinates and bounds.

Saved work: 36/36 native batches, 72/72 linear programs and 144/288 exact proposal checks. Reporting performs no new integrations.

| Model | Processing case | North direction | Radius .001 | Radius .0005 | Radius .00025 |
|---|---|---|---|---|---|
| Globe + field | Zero removal | Negative | Usable | Usable | Usable |
| Globe + field | Zero removal | Positive | Usable | Usable | Usable |
| Globe + field | Profiled removal | Negative | Usable | Usable | Usable |
| Globe + field | Profiled removal | Positive | Usable | Usable | Usable |
| Globe, zero field | Zero removal | Negative | Usable | Usable | Usable |
| Globe, zero field | Zero removal | Positive | Usable | Usable | Usable |
| Globe, zero field | Profiled removal | Negative | Usable | Usable | Usable |
| Globe, zero field | Profiled removal | Positive | Usable | Usable | Usable |
| Stationary disc | Zero removal | Negative | Rejected | Usable | Usable |
| Stationary disc | Zero removal | Positive | Usable | Usable | Usable |
| Stationary disc | Profiled removal | Negative | Rejected | Usable | Usable |
| Stationary disc | Profiled removal | Positive | Usable | Usable | Usable |

## What this establishes

These are generated trajectories, not aircraft results. A usable step must satisfy the actual earlier position limits and make the predicted directional progress. A rejected step remains in the record.

Earlier accepted probes remain valid: their north spreads are **13.33 m** and **5.90 m**. All six accepted and six rejected original labels were rechecked without a new native evaluation.

Passing this trial qualifies only the first-step component. It does not establish a complete optimizer, outer prediction bounds, a calibrated error model or adequate aircraft predictions. **V01 remains unqualified.** The 53-stretch numerical findings are unchanged.

[Frozen method and limits](PLAN.md) · [Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
